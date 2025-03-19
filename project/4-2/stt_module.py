# -*- coding:utf-8 -*-
# 科大讯飞语音识别WebSocket API简化版
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

# 确保使用正确的websocket库
from websocket import WebSocketApp

# 帧状态定义
STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

class XfyunSTT:
    """科大讯飞语音识别WebSocket API封装类"""
    
    def __init__(self, app_id, api_key, api_secret):
        self.APPID = app_id
        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.ws_url = "wss://ws-api.xfyun.cn/v2/iat"
        self.result = ""
        self.result_complete = False
        
    def create_url(self):
        """生成鉴权URL"""
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        
        # 进行hmac-sha256加密
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
        
        # 拼接鉴权参数,生成url
        url = self.ws_url + '?' + urlencode(v)
        return url
    
    def on_message(self, ws, message):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            code = data["code"]
            
            if code != 0:
                print(f"错误: {data['message']}, 代码: {code}")
                ws.close()
                return
                
            # 解析识别结果
            if "data" in data and "result" in data["data"]:
                result_data = data["data"]["result"]
                
                # 如果是最终结果
                if "ws" in result_data:
                    words = result_data["ws"]
                    text = ""
                    for word in words:
                        for cw in word["cw"]:
                            text += cw["w"]
                    
                    # 添加到当前结果
                    self.result += text
                    print(f"当前识别结果: {self.result}")
                
                # 判断是否是最后一个结果
                if data["data"].get("status") == 2:
                    self.result_complete = True
                    ws.close()
            
        except Exception as e:
            print(f"解析消息异常: {e}")
    
    def on_error(self, ws, error):
        """处理错误"""
        print(f"错误: {error}")
    
    def on_close(self, ws, close_status_code=None, close_msg=None):
        """处理连接关闭"""
        print("连接已关闭")
    
    def on_open(self, ws, audio_file):
        """处理连接建立"""
        def run():
            # 读取音频文件准备发送
            self._send_audio_data(ws, audio_file)
        
        # 创建线程发送数据
        threading.Thread(target=run).start()
    
    def _send_audio_data(self, ws, audio_file):
        """发送音频数据"""
        print(f"准备读取音频文件: {audio_file}")
        
        # 音频参数设置
        frame_size = 8000  # 每一帧的音频大小
        interval = 0.04    # 发送音频间隔(单位:s)
        status = STATUS_FIRST_FRAME  # 音频的状态信息
        
        # 准备通用参数和业务参数
        common_args = {"app_id": self.APPID}
        business_args = {
            "domain": "iat", 
            "language": "zh_cn", 
            "accent": "mandarin", 
            "vinfo": 1,
            "vad_eos": 10000
        }
        
        with open(audio_file, 'rb') as fp:
            while True:
                buf = fp.read(frame_size)
                
                # 文件结束
                if not buf:
                    status = STATUS_LAST_FRAME
                
                # 第一帧处理
                if status == STATUS_FIRST_FRAME:
                    d = {
                        "common": common_args,
                        "business": business_args,
                        "data": {
                            "status": 0, 
                            "format": "audio/L16;rate=16000",
                            "audio": str(base64.b64encode(buf), 'utf-8'),
                            "encoding": "raw"
                        }
                    }
                    ws.send(json.dumps(d))
                    status = STATUS_CONTINUE_FRAME
                    print("发送第一帧数据")
                
                # 中间帧处理
                elif status == STATUS_CONTINUE_FRAME:
                    d = {
                        "data": {
                            "status": 1, 
                            "format": "audio/L16;rate=16000",
                            "audio": str(base64.b64encode(buf), 'utf-8'),
                            "encoding": "raw"
                        }
                    }
                    ws.send(json.dumps(d))
                    
                # 最后一帧处理
                elif status == STATUS_LAST_FRAME:
                    d = {
                        "data": {
                            "status": 2, 
                            "format": "audio/L16;rate=16000",
                            "audio": str(base64.b64encode(buf), 'utf-8'),
                            "encoding": "raw"
                        }
                    }
                    ws.send(json.dumps(d))
                    print("发送最后一帧数据")
                    break
                    
                # 模拟音频采样间隔
                time.sleep(interval)

    def recognize(self, audio_file):
        """从音频文件识别文本"""
        # 先检查文件是否存在
        if not os.path.exists(audio_file):
            print(f"错误: 音频文件 {audio_file} 不存在")
            return None
            
        # 重置结果
        self.result = ""
        self.result_complete = False
        
        # 创建WebSocket连接
        wsUrl = self.create_url()
        
        print(f"识别音频文件: {audio_file}")
        print("连接科大讯飞WebSocket API...")
        
        # 创建WebSocket对象
        ws = WebSocketApp(
            wsUrl,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        # 设置回调
        def on_open_with_args(ws):
            self.on_open(ws, audio_file)
        
        ws.on_open = on_open_with_args
        
        # 运行WebSocket连接
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        print(f"识别完成,文本结果: {self.result}")
        return self.result
    
    def convert_audio_to_wav(self, input_file, output_file=None):
        """将各种音频格式转换为WAV格式（需要安装pydub）"""
        try:
            from pydub import AudioSegment
            
            # 根据扩展名确定格式
            ext = os.path.splitext(input_file)[1].lower()
            
            # 如果未指定输出文件名,使用相同名称但改为.wav扩展名
            if not output_file:
                output_file = os.path.splitext(input_file)[0] + '.wav'
            
            # 加载音频文件
            if ext == '.mp3':
                audio = AudioSegment.from_mp3(input_file)
            elif ext == '.wav':
                return input_file  # 如果已经是WAV文件,直接返回
            elif ext == '.flac':
                audio = AudioSegment.from_file(input_file, "flac")
            elif ext == '.ogg':
                audio = AudioSegment.from_ogg(input_file)
            elif ext == '.aac':
                audio = AudioSegment.from_file(input_file, "aac")
            elif ext == '.m4a':
                audio = AudioSegment.from_file(input_file, "m4a")
            else:
                audio = AudioSegment.from_file(input_file)
            
            # 转换为16kHz采样率、单声道
            audio = audio.set_frame_rate(16000).set_channels(1)
            
            # 导出为WAV文件
            audio.export(output_file, format="wav")
            print(f"音频已转换为WAV格式: {output_file}")
            return output_file
            
        except ImportError:
            print("警告: 未安装pydub库,无法转换音频格式.")
            print("请使用以下命令安装: pip install pydub")
            return input_file
        except Exception as e:
            print(f"音频转换失败: {e}")
            return input_file


def recognize_speech(audio_file):
    """使用讯飞STT识别音频文件"""
    APP_ID = "23fb26ce"
    API_KEY = "d5048d7e56593d679d174153c48a78f9"
    API_SECRET = "MjAzNjI5ZTU3MzhjNTdkY2QzZmE4Y2Nh"
    
    # 检查文件是否存在
    if not os.path.exists(audio_file):
        print(f"错误: 音频文件 {audio_file} 不存在")
        return None
    
    # 创建识别对象
    stt = XfyunSTT(APP_ID, API_KEY, API_SECRET)
    
    # 尝试转换音频格式（如果不是WAV格式）
    if not audio_file.lower().endswith('.wav'):
        print("检测到非WAV格式音频,尝试转换...")
        wav_file = stt.convert_audio_to_wav(audio_file)
        if wav_file != audio_file:
            audio_file = wav_file
        else:
            print("警告: 无法转换音频格式,将尝试直接使用原始文件,但可能无法正确识别")
    
    # 开始识别
    start_time = datetime.now()
    result = stt.recognize(audio_file)
    end_time = datetime.now()
    
    if result:
        print(f"\n识别结果: {result}")
        print(f"识别耗时: {end_time - start_time}")
        return result
    else:
        print("识别失败")
        return None