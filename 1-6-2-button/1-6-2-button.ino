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

//------------------------ 硬件配置部分 ------------------------//
#define BUTTON_PIN      16
#define STATUS_LED_PIN  2
volatile bool buttonPressed = false;  // 中断标志位
bool isRecording = false;             // 录音状态标志

//------------------------ 音频配置部分 ------------------------//
#define I2S_NUM         I2S_NUM_0
#define SAMPLE_RATE     44100
#define BITS_PER_SAMPLE I2S_BITS_PER_SAMPLE_16BIT
#define BUFFER_SIZE     512
#define MIC_WS_PIN      27
#define MIC_SCK_PIN     26
#define MIC_SD_PIN      13
#define SPK_DIN_PIN     25
const float GAIN = 3.0;

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
  http.setTimeout(8000);
  http.begin(apiUrl);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", "Bearer " + String(apiKey));

  DynamicJsonDocument payloadDoc(1024);
  JsonArray messages = payloadDoc.createNestedArray("messages");
  JsonObject message = messages.createNestedObject();
  message["role"] = "user";
  message["content"] = inputText;
  payloadDoc["model"] = "glm-4-flashx";

  String payload;
  serializeJson(payloadDoc, payload);

  int httpCode = http.POST(payload);
  String response = http.getString();

  if (httpCode == HTTP_CODE_OK) {
    DynamicJsonDocument doc(2048);
    deserializeJson(doc, response);
    return doc["choices"][0]["message"]["content"].as<String>();
  }
  return "[API错误:" + String(httpCode) + "]";
}

//------------------------ 初始化部分 ------------------------//
void setup() {
  Serial.begin(115200);
  pinMode(STATUS_LED_PIN, OUTPUT);
  digitalWrite(STATUS_LED_PIN, LOW);

  // WiFi连接
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

  // 音频系统初始化
  esp_err_t err = i2s_driver_install(I2S_NUM, &i2s_config, 0, NULL);
  if(err != ESP_OK) Serial.printf("I2S初始化失败:0x%X\n", err);
  
  err = i2s_set_pin(I2S_NUM, &pin_config);
  if(err != ESP_OK) Serial.printf("引脚配置失败:0x%X\n", err);
  
  i2s_set_clk(I2S_NUM, SAMPLE_RATE, BITS_PER_SAMPLE, I2S_CHANNEL_MONO);
  Serial.println("音频系统就绪");

  // 按钮初始化
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), []() {
    static unsigned long lastPress = 0;
    if (millis() - lastPress > 50) {
      buttonPressed = true;
    }
    lastPress = millis();
  }, FALLING);
}

//------------------------ 主程序部分 ------------------------//
void loop() {
  // 按钮状态处理
  if (buttonPressed) {
    buttonPressed = false;
    isRecording = !isRecording;
    digitalWrite(STATUS_LED_PIN, isRecording ? HIGH : LOW);
    Serial.println(isRecording ? "开始录音回放" : "停止录音回放");
  }

  // 音频处理（仅在录音状态时工作）
  if (isRecording) {
    static int16_t audioBuffer[BUFFER_SIZE];
    size_t bytesRead;
    
    if (i2s_read(I2S_NUM, audioBuffer, sizeof(audioBuffer), &bytesRead, 0) == ESP_OK) {
      for (int i = 0; i < bytesRead / 2; i++) {
        audioBuffer[i] = constrain(audioBuffer[i] * GAIN, -32768, 32767);
      }
      
      size_t bytesWritten;
      i2s_write(I2S_NUM, audioBuffer, bytesRead, &bytesWritten, 0);
    }
  }

  // 串口处理（保持不变）
  static String inputBuffer;
  while (Serial.available() > 0) {
    char c = Serial.read();
    
    if(c == '\r' || c == '\n') {
      if(inputBuffer.length() > 0) {
        inputBuffer.trim();
        Serial.print("思考中...");
        String response = getGPTAnswer(inputBuffer);
        Serial.println("\n智谱清言：" + response);
        inputBuffer = "";
      }
      while(Serial.available() > 0) Serial.read();
    } 
    else if(c >= 32 || (uint8_t)c >= 0xA0) {
      inputBuffer += c;
    }
  }
}
