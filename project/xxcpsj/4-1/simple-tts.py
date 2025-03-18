# -*- coding:utf-8 -*-
# 科大讯飞语音合成WebSocket API简化版
# 只需要安装: pip install websocket-client

import base64
import hashlib
import hmac
import json
import os
import ssl
import time
import threading
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

# 修改导入语句，确保使用正确的websocket库
from websocket import WebSocketApp

class XfyunTTS:
    """科大讯飞语音合成WebSocket API封装类"""
    
    def __init__(self, app_id, api_key, api_secret):
        self.APPID = app_id
        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.TEXT = ""
        self.audio_data = bytearray()
        self.ws_url = "wss://tts-api.xfyun.cn/v2/tts"
        
    def set_text(self, text):
        """设置要合成的文本"""
        self.TEXT = text
        
    def create_url(self):
        """生成鉴权URL"""
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
        
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.API_SECRET.encode('utf-8'), 
                                 signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.API_KEY, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        
        # 拼接鉴权参数，生成url
        url = self.ws_url + '?' + urlencode(v)
        return url
    
    def on_message(self, ws, message):
        """处理接收到的消息"""
        message = json.loads(message)
        code = message["code"]
        if code != 0:
            print(f"错误: {message['message']}, 代码: {code}")
            ws.close()
            return
            
        audio = message["data"]["audio"]
        status = message["data"]["status"]
        
        # 解码音频数据并追加
        audio_data = base64.b64decode(audio)
        self.audio_data.extend(audio_data)
        
        if status == 2:  # 最后一帧
            print("语音合成完成")
            ws.close()
    
    def on_error(self, ws, error):
        """处理错误"""
        print(f"错误: {error}")
    
    def on_close(self, ws, close_status_code=None, close_msg=None):
        """处理连接关闭"""
        print("连接已关闭")
    
    def on_open(self, ws):
        """处理连接建立"""
        def run(*args):
            # Base64编码文本
            text_b64 = str(base64.b64encode(self.TEXT.encode('utf-8')), "UTF8")
            
            d = {
                "common": {
                    "app_id": self.APPID
                },
                "business": {
                    "aue": "raw",  # raw: pcm格式
                    "auf": "audio/L16;rate=16000",  # 16k采样率
                    "vcn": "xiaoyan",  # 发音人
                    "tte": "utf8"  # 文本编码
                },
                "data": {
                    "status": 2,  # 2表示完整的一段文本
                    "text": text_b64
                }
            }
            
            ws.send(json.dumps(d))
            print("文本数据已发送，等待合成...")
        
        # 创建线程发送数据
        threading.Thread(target=run).start()

    def synthesize(self, text, output_file="output.wav"):
        """合成语音"""
        self.set_text(text)
        self.audio_data = bytearray()  # 清空之前的音频数据
        
        # 创建WebSocket连接
        wsUrl = self.create_url()
        
        print(f"合成文本: {text}")
        print("连接科大讯飞WebSocket API...")
        
        # 创建WebSocket对象，使用正确导入的WebSocketApp
        ws = WebSocketApp(
            wsUrl,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        ws.on_open = self.on_open
        
        # 运行WebSocket连接，设置SSL选项
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        # 检查是否有音频数据
        if len(self.audio_data) == 0:
            print("合成失败，未接收到音频数据")
            return False
        
        # 根据文件扩展名选择保存方式
        ext = os.path.splitext(output_file)[1].lower()
        
        if ext == '.pcm':
            # 保存为PCM文件
            with open(output_file, 'wb') as f:
                f.write(self.audio_data)
            print(f"已保存PCM文件: {os.path.abspath(output_file)}")
            
        elif ext == '.wav':
            # 转换为WAV格式 (添加WAV头)
            self._save_as_wav(output_file)
            print(f"已保存WAV文件: {os.path.abspath(output_file)}")
            
        else:
            # 默认保存为PCM
            pcm_file = output_file + ".pcm"
            with open(pcm_file, 'wb') as f:
                f.write(self.audio_data)
            print(f"已保存PCM文件: {os.path.abspath(pcm_file)}")
            
        return True
            
    def _save_as_wav(self, filename):
        """将PCM数据保存为WAV文件"""
        # 创建简单的WAV文件头
        # 参数: 声道数=1, 采样宽度=2, 采样率=16000, 帧数, 压缩类型, 压缩名称
        import wave
        
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(1)  # 单声道
            wav_file.setsampwidth(2)  # 16bit (2字节)采样宽度
            wav_file.setframerate(16000)  # 16kHz采样率
            wav_file.writeframes(self.audio_data)


def main():
    """主函数示例"""
    # 请替换为您的API凭证
    APP_ID = "23fb26ce"
    API_KEY = "d5048d7e56593d679d174153c48a78f9"
    API_SECRET = "MjAzNjI5ZTU3MzhjNTdkY2QzZmE4Y2Nh"
    
    tts = XfyunTTS(APP_ID, API_KEY, API_SECRET)
    
    # 测试中文文本合成
    text = "你好，我是科大讯飞"
    output_file = "output.wav"  # 可以是 .wav 或 .pcm 文件
    
    print(f"准备合成文本: '{text}'")
    
    # 开始合成
    success = tts.synthesize(text, output_file)
    
    if success:
        print(f"合成成功！文件保存在: {os.path.abspath(output_file)}")
    else:
        print("合成失败！")


if __name__ == "__main__":
    main()
    