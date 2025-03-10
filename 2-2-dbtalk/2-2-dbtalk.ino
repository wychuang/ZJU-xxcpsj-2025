#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <driver/i2s.h>
#include <time.h>  // 添加时间库

//------------------------ 网络配置部分 ------------------------//
const char* wifi_name = "group09";
const char* wifi_password = "11235813";
const char* apiKey = "afc452477e984636a61c2a403ca21138.SHMSzCsrJ8IPoRz2";
String inputText = "你好，智谱清言！";
String apiUrl = "https://open.bigmodel.cn/api/paas/v4/chat/completions";
String pcUrl = "http://192.168.54.6:5001/store_message"; // PC端存储API地址
String answer;

// NTP服务器配置
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 8 * 3600;  // 中国时区 (GMT+8)
const int daylightOffset_sec = 0;

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

// 获取当前时间的格式化字符串
String getFormattedTime() {
  struct tm timeinfo;
  char timeStringBuff[30];
  
  if(!getLocalTime(&timeinfo)){
    Serial.println("获取时间失败");
    return "Unknown";
  }
  
  // 格式: 2025-03-10 21:18:05
  strftime(timeStringBuff, sizeof(timeStringBuff), "%Y-%m-%d %H:%M:%S", &timeinfo);
  return String(timeStringBuff);
}

// 发送对话数据到PC存储
bool sendConversationToPC(String userInput, String modelResponse) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi未连接，无法发送数据");
    return false;
  }

  Serial.print("正在连接到PC: ");
  Serial.println(pcUrl);

  HTTPClient http;
  http.begin(pcUrl);
  http.addHeader("Content-Type", "application/json");
  
  // 创建JSON对象
  DynamicJsonDocument doc(2048);
  doc["timestamp"] = getFormattedTime();  // 添加时间戳
  doc["user_input"] = userInput;
  doc["model_response"] = modelResponse;
  
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  Serial.println("发送数据: " + jsonPayload);
  
  int httpCode = http.POST(jsonPayload);
  String response = http.getString();
  http.end();
  
  if (httpCode == 200) {
    Serial.println("对话数据成功保存到PC");
    return true;
  } else {
    Serial.print("发送数据到PC失败，HTTP错误码: ");
    Serial.println(httpCode);
    Serial.print("响应内容: ");
    Serial.println(response);
    return false;
  }
}

// 单独的函数用于测试PC连接
void testPCConnection() {
  Serial.println("\n测试PC连接...");
  HTTPClient http;
  http.begin(pcUrl);
  http.addHeader("Content-Type", "application/json");
  
  // 创建一个简单的测试JSON
  DynamicJsonDocument testDoc(512);
  testDoc["timestamp"] = getFormattedTime();  // 添加时间戳
  testDoc["user_input"] = "连接测试";
  testDoc["model_response"] = "这是一个ESP32连接测试";
  
  String testPayload;
  serializeJson(testDoc, testPayload);
  
  int httpCode = http.POST(testPayload);
  String response = http.getString();
  http.end();
  
  if (httpCode == 200) {
    Serial.println("PC连接测试成功！");
  } else {
    Serial.print("PC连接测试失败，HTTP错误码: ");
    Serial.println(httpCode);
    Serial.print("响应内容: ");
    Serial.println(response);
  }
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
  http.end();

  if (httpCode == HTTP_CODE_OK) {
    DynamicJsonDocument doc(2048);
    deserializeJson(doc, response);
    String answer = doc["choices"][0]["message"]["content"].as<String>();
    
    // 获取到回答后，将对话发送到PC存储
    sendConversationToPC(inputText, answer);
    
    return answer;
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
    
    // 配置NTP服务器，同步时间
    configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
    Serial.println("正在同步时间...");
    delay(1000);
    Serial.print("当前时间: ");
    Serial.println(getFormattedTime());
    
    // 在获取AI回答前先测试PC连接
    testPCConnection();
    
    Serial.println("首次问候:");
    String initialAnswer = getGPTAnswer(inputText);
    Serial.println(initialAnswer);
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

  // 串口处理
  static String inputBuffer;
  while (Serial.available() > 0) {
    char c = Serial.read();
    
    if(c == '\r' || c == '\n') {
      if(inputBuffer.length() > 0) {
        inputBuffer.trim();
        String userQuestion = inputBuffer;
        Serial.print("思考中...");
        String response = getGPTAnswer(userQuestion);
        Serial.println("\n智谱清言：" + response);
        
        inputBuffer = "";
      }
      while(Serial.available() > 0) Serial.read();
    } 
    else if(c >= 32 || (uint8_t)c >= 0xA0) {
      inputBuffer += c;
    }
  }
  
  // 检查WiFi连接状态
  static unsigned long lastWiFiCheck = 0;
  if (millis() - lastWiFiCheck > 30000) { // 每30秒检查一次
    lastWiFiCheck = millis();
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi连接断开，尝试重连...");
      WiFi.begin(wifi_name, wifi_password);
    }
  }
}