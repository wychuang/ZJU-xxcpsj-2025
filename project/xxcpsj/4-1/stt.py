import websocket
import datetime
import hashlib
import base64
import hmac
import json
import time
import ssl
import threading
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import pyaudio
import wave

# 以下为WebAPI的常量参数
API_URL = "ws://rtasr.xfyun.cn/v1/ws"  # 实时语音转写服务地址
APP_ID = "您的APPID"
API_KEY = "您的APIKey"
API_SECRET = "您的APISecret"

# 录音参数
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

class IflytekSpeechRecognizer:
    def __init__(self):
        # websocket客户端
        self.ws = None
        # 识别结果
        self.result = ""
        
    def _generate_signature(self, date):
        """生成请求签名"""
        signature_origin = f"host: rtasr.xfyun.cn\ndate: {date}\nGET /v1/ws HTTP/1.1"
        signature_sha = hmac.new(API_SECRET.encode('utf-8'), 
                                 signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = f'api_key="{API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        return authorization
    
    def _build_auth_url(self):
        """构建鉴权URL"""
        现在 = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature = self._generate_signature(date)
        auth_url = API_URL + "?" + urlencode({
            'host': 'rtasr.xfyun.cn',
            'date': date,
            'authorization': signature
        })
        return auth_url
    
    def _on_message(self, ws, message):
        """接收消息回调"""
        data = json.loads(message)
        if data["action"] == "result":
            result = json.loads(data["data"])
            # 解析结果
            if result["cn"]["st"]["type"] == "0":
                self.result += result["cn"]["st"]["rt"][0]["ws"][0]["cw"][0]["w"]
                print("识别结果:", self.result)
    
    def _on_error(self, ws, error):
        """错误回调"""
        print("错误:", error)
    
    def _on_close(self, ws, close_status_code, close_reason):
        """关闭连接回调"""
        print("连接关闭")
    
    def _on_open(self, ws):
        """连接建立回调"""
        print("连接已建立")
        # 开始发送音频数据线程
        def send_audio_data():
            # 打开音频文件
            with wave.open(WAVE_OUTPUT_FILENAME, 'rb') as wf:
                # 读取音频数据
                audio_data = wf.readframes(wf.getnframes())
                # 发送音频数据
                self.ws.send(audio_data, websocket.ABNF.OPCODE_BINARY)
                print("音频数据已发送")
                # 发送结束标记
                self.ws.send('{"end": true}')
                
        threading.Thread(target=send_audio_data).start()
    
    def record_audio(self):
        """录制音频"""
        p = pyaudio.PyAudio()
        
        print("开始录音...")
        
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
        
        frames = []
        
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
        
        print("录音结束")
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # 将录音数据保存为WAV文件
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        print(f"录音已保存为 {WAVE_OUTPUT_FILENAME}")
    
    def recognize_from_file(self, audio_file=WAVE_OUTPUT_FILENAME):
        """从文件识别语音"""
        # 构建鉴权URL
        auth_url = self._build_auth_url()
        
        # 设置websocket
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(auth_url,
                                        on_open=self._on_open,
                                        on_message=self._on_message,
                                        on_error=self._on_error,
                                        on_close=self._on_close)
        
        # 启动websocket连接
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        return self.result
    
    def recognize_speech(self):
        """录音并识别"""
        self.record_audio()
        return self.recognize_from_file()

# 使用示例
if __name__ == "__main__":
    recognizer = IflytekSpeechRecognizer()
    text = recognizer.recognize_speech()
    print("最终识别结果:", text)