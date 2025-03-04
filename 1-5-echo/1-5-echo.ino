#include <Arduino.h>
#include <driver/i2s.h>

// I2S配置参数
#define I2S_NUM         I2S_NUM_0
#define SAMPLE_RATE     44100
#define BITS_PER_SAMPLE I2S_BITS_PER_SAMPLE_16BIT
#define BUFFER_SIZE     512  // 增大缓冲区提升稳定性

// 引脚定义（根据最新硬件连接）
#define MIC_WS_PIN      27   // 保持WS引脚不变
#define MIC_SCK_PIN     26   // BCLK修改为26
#define MIC_SD_PIN      13
#define SPK_DIN_PIN     25

// I2S全双工配置
i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX | I2S_MODE_TX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = BITS_PER_SAMPLE,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 256,  // 优化DMA长度
    .use_apll = true,    // 启用APLL提升时钟精度
    .tx_desc_auto_clear = true
};

// 统一时钟配置
i2s_pin_config_t pin_config = {
    .bck_io_num = MIC_SCK_PIN,
    .ws_io_num = MIC_WS_PIN,
    .data_out_num = SPK_DIN_PIN,
    .data_in_num = MIC_SD_PIN
};

void setup() {
    Serial.begin(115200);
    Serial.println("System Init Start...");
    
    // I2S驱动初始化
    esp_err_t err = i2s_driver_install(I2S_NUM, &i2s_config, 0, NULL);
    if(err != ESP_OK){
        Serial.printf("I2S Init Failed! Error: 0x%X\n", err);
        while(1) delay(100);
    }
    
    err = i2s_set_pin(I2S_NUM, &pin_config);
    if(err != ESP_OK){
        Serial.printf("Pin Config Failed! Error: 0x%X\n", err);
        while(1) delay(100);
    }
    
    // 设置时钟同步（关键修正）
    i2s_set_clk(I2S_NUM, SAMPLE_RATE, BITS_PER_SAMPLE, I2S_CHANNEL_MONO);
    Serial.println("I2S Init Success @44.1kHz 16bit Mono");
}

void loop() {
    static uint32_t loopCount = 0;
    int16_t* buffer = (int16_t*)malloc(BUFFER_SIZE * sizeof(int16_t));
    
    if(!buffer){
        Serial.println("Memory Allocation Error!");
        delay(1000);
        return;
    }

    // 音频采集阶段
    size_t bytesRead;
    esp_err_t readErr = i2s_read(I2S_NUM, buffer, BUFFER_SIZE*sizeof(int16_t), &bytesRead, portMAX_DELAY);
    if(readErr == ESP_OK){
        Serial.printf("[%lu] Captured: %d bytes\n", ++loopCount, bytesRead);
    }else{
        Serial.printf("Read Error: 0x%X\n", readErr);
    }
    // 放大音频信号
    const float GAIN = 10.0; // 调整增益（例如 2.0 表示放大两倍）
    for (int i = 0; i < bytesRead / sizeof(int16_t); i++) {
        buffer[i] = buffer[i] * GAIN;
        buffer[i] = constrain(buffer[i], -32768, 32767); // 防止溢出
    }
    // 音频回放阶段
    size_t bytesWritten;
    esp_err_t writeErr = i2s_write(I2S_NUM, buffer, bytesRead, &bytesWritten, portMAX_DELAY);
    if(writeErr == ESP_OK){
        Serial.printf("[%lu] Playback: %d bytes\n", loopCount, bytesWritten);
    }else{
        Serial.printf("Write Error: 0x%X\n", writeErr);
    }

    free(buffer);
    
    // 状态监控
    if(loopCount % 50 == 0){
        size_t freeHeap = esp_get_free_heap_size();
        Serial.printf("System Status - Free Heap: %d bytes\n", freeHeap);
    }
}