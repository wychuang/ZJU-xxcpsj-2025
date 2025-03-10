#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <driver/i2s.h>

//------------------------ 网络配置部分 ------------------------//
const char* wifi_name = "group09";
const char* wifi_password = "11235813";
const char* apiKey = "afc452477e984636a61c2a403ca21138.SHMSzCsrJ8IPoRz2";
String inputText = "你好，智谱清言！";
String apiUrl = "https://open.bigmodel.cn/api/paas/v4/chat/completions";
String answer;

//------------------------ 音频配置部分 ------------------------//
#define I2S_NUM         I2S_NUM_0
#define SAMPLE_RATE     44100
#define BITS_PER_SAMPLE I2S_BITS_PER_SAMPLE_16BIT
#define BUFFER_SIZE     512
#define MIC_WS_PIN      27
#define MIC_SCK_PIN     26
#define MIC_SD_PIN      13
#define SPK_DIN_PIN     25
const float GAIN = 3.0;  // 降低增益避免爆音

i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX | I2S_MODE_TX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = BITS_PER_SAMPLE,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 256,
    .use_apll = true,
    .tx_desc_auto_clear = true
};

i2s_pin_config_t pin_config = {
    .bck_io_num = MIC_SCK_PIN,
    .ws_io_num = MIC_WS_PIN,
    .data_out_num = SPK_DIN_PIN,
    .data_in_num = MIC_SD_PIN
};

//------------------------ 功能函数部分 ------------------------//
void printWiFiInfo() {
  Serial.println("\n网络信息:");
  Serial.print("IP地址: "); Serial.println(WiFi.localIP());
  Serial.print("信号强度: "); Serial.print(WiFi.RSSI()); Serial.println(" dBm");
}

String getGPTAnswer(String inputText) {
  HTTPClient http;
  http.setTimeout(8000);  // 设置更短的超时时间
  http.begin(apiUrl);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", "Bearer " + String(apiKey));

  // 使用ArduinoJson构建JSON请求体
  DynamicJsonDocument payloadDoc(1024);
  JsonArray messages = payloadDoc.createNestedArray("messages");
  JsonObject message = messages.createNestedObject();
  message["role"] = "user";
  message["content"] = inputText;
  payloadDoc["model"] = "glm-4-flashx";

  String payload;
  serializeJson(payloadDoc, payload);

  // 打印请求体
  //Serial.println("请求体: " + payload);

  int httpCode = http.POST(payload);
  String response = http.getString();

  // 打印响应内容
  //Serial.println("响应内容: " + response);

  if (httpCode == HTTP_CODE_OK) {
    DynamicJsonDocument doc(2048);
    deserializeJson(doc, response);
    return doc["choices"][0]["message"]["content"].as<String>();
  }
  return "[API错误:" + String(httpCode) + "]";
}

//------------------------ 主程序部分 ------------------------//
void setup() {
  Serial.begin(115200);
  
  // 第一阶段：网络连接
  Serial.println("正在连接WiFi...");
  WiFi.begin(wifi_name, wifi_password);
  
  uint8_t wifiRetries = 0;
  while (WiFi.status() != WL_CONNECTED && wifiRetries++ < 15) {
    delay(500);
    Serial.print(".");
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    printWiFiInfo();
    Serial.println("首次问候:");
    Serial.println(getGPTAnswer(inputText));
  } else {
    Serial.println("\nWiFi连接失败，仅启用音频功能");
  }

  // 第二阶段：音频系统初始化
  esp_err_t err = i2s_driver_install(I2S_NUM, &i2s_config, 0, NULL);
  if(err != ESP_OK) Serial.printf("I2S初始化失败:0x%X\n", err);
  
  err = i2s_set_pin(I2S_NUM, &pin_config);
  if(err != ESP_OK) Serial.printf("引脚配置失败:0x%X\n", err);
  
  i2s_set_clk(I2S_NUM, SAMPLE_RATE, BITS_PER_SAMPLE, I2S_CHANNEL_MONO);
  Serial.println("音频系统就绪");
}
void loop() {
    // 音频处理核心（实时优先）
    static int16_t audioBuffer[BUFFER_SIZE];  // 静态内存分配
    size_t bytesRead;

    if (i2s_read(I2S_NUM, audioBuffer, sizeof(audioBuffer), &bytesRead, 0) == ESP_OK) {
        // 音频处理流水线
        for (int i = 0; i < bytesRead / 2; i++) {
            audioBuffer[i] = constrain(audioBuffer[i] * GAIN, -32768, 32767);
        }

        // 实时回放
        size_t bytesWritten;
        i2s_write(I2S_NUM, audioBuffer, bytesRead, &bytesWritten, 0);
    }

    // 非阻塞式串口处理
static String inputBuffer;
  while (Serial.available() > 0) {
    char c = Serial.read();
    
    // 调试输出原始输入
    Serial.printf("[RAW] %02X ", c); // 打印ASCII码
    
    if(c == '\r' || c == '\n') {
      if(inputBuffer.length() > 0) {
        //Serial.println("\n收到有效输入");
        inputBuffer.trim(); // 清除不可见字符
        
        // 在串口中print原数据
        //Serial.printf("实际输入内容 (%d字节): ", inputBuffer.length());
        //for(int i=0; i<inputBuffer.length(); i++){
        //  Serial.printf("%02X ", inputBuffer[i]);
        //}
        //Serial.println("\n文本显示: " + inputBuffer);

        // 执行API请求
        Serial.print("思考中...");
        String response = getGPTAnswer(inputBuffer);
        Serial.println("\n智谱清言：" + response);
        
        inputBuffer = "";
      }
      while(Serial.available() > 0) Serial.read(); // 清空输入缓存
    } 
    else if(c >= 32 || (uint8_t)c >= 0xA0) { // 允许中文和可见ASCII
      inputBuffer += c;
    }
  }
}
