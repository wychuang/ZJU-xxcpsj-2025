import base64
import hashlib
import hmac
import json
import os
import time
import urllib.parse
import urllib.request
import wave

class IflytekTTS:
    def __init__(self):
        # API参数设置
        self.APPID = "您的APPID"
        self.API_KEY = "您的APIKey"
        self.API_SECRET = "您的APISecret"
        self.TTS_URL = "http://api.xfyun.cn/v1/service/v1/tts"
        
        # 音频参数
        self.AUE = "raw"  # 音频编码，raw(pcm)、wav、mp3
        self.VOICE_NAME = "xiaoyan"  # 发音人，可选，默认为小燕
        self.SAMPLE_RATE = 16000  # 采样率，可选，默认为16000
        self.SPEED = 50  # 语速，可选，默认为50
        self.VOLUME = 50  # 音量，可选，默认为50
        self.PITCH = 50  # 音高，可选，默认为50
        self.ENGINE_TYPE = "intp65"  # 引擎类型，可选，默认为intp65
        
    def _create_url(self):
        """构建鉴权URL"""
        # 当前时间戳
        current_time = str(int(time.time()))
        # 准备参数
        param = {
            "auf": "audio/L16;rate=16000",
            "aue": self.AUE,
            "voice_name": self.VOICE_NAME,
            "speed": self.SPEED,
            "volume": self.VOLUME,
            "pitch": self.PITCH,
            "engine_type": self.ENGINE_TYPE,
            "text_type": "text"
        }
        
        # 将参数编码
        param_base64 = base64.b64encode(json.dumps(param).encode('utf-8'))
        
        # 拼接字符串
        signature_origin = self.API_KEY + current_time + param_base64.decode()
        
        # 使用hmac-sha1生成签名
        signature = hmac.new(
            self.API_SECRET.encode(),
            signature_origin.encode(),
            digestmod=hashlib.sha1
        ).digest()
        
        # Base64编码签名
        signature = base64.b64encode(signature).decode()
        
        # 构建请求头
        header = {
            "X-CurTime": current_time,
            "X-Param": param_base64.decode(),
            "X-Appid": self.APPID,
            "X-SignType": "sha1",
            "X-CheckSum": signature,
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
        }
        
        return header
    
    def text_to_speech(self, text, output_file="output.wav"):
        """将文本转换为语音"""
        # 构建请求头
        header = self._create_url()
        
        # 编码文本
        text = urllib.parse.quote_plus(text)
        body = f"text={text}"
        
        # 发送请求
        req = urllib.request.Request(self.TTS_URL, body.encode('utf-8'), header)
        
        try:
            response = urllib.request.urlopen(req)
            content = response.read()
            
            # 如果是WAV格式，需要添加头信息
            if self.AUE == "raw":
                # 添加 WAV 头信息
                with wave.open(output_file, 'wb') as wav_file:
                    wav_file.setparams((1, 2, self.SAMPLE_RATE, 0, 'NONE', 'NONE'))
                    wav_file.writeframes(content)
            else:
                # 直接写入文件
                with open(output_file, 'wb') as f:
                    f.write(content)
            
            print(f"语音合成成功，已保存到 {output_file}")
            return True
        
        except Exception as e:
            print(f"语音合成失败: {e}")
            return False

# 使用示例
if __name__ == "__main__":
    tts = IflytekTTS()
    text = "科大讯飞语音合成测试，效果非常好。"
    tts.text_to_speech(text, "output.wav")