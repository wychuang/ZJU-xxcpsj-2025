#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pyaudio
import wave
import os
import time

def record_audio(file_name="input.wav", seconds=5, sample_rate=16000):
    """
    录制音频文件
    
    Args:
        file_name (str): 输出文件名
        seconds (int): 录制时长（秒）
        sample_rate (int): 采样率
    """
    # 音频参数设置
    chunk = 1024
    audio_format = pyaudio.paInt16
    channels = 1
    
    # 初始化PyAudio
    p = pyaudio.PyAudio()
    
    print(f"准备录制 {seconds} 秒的音频...")
    print("3秒后开始录制，请准备好您的问题...")
    
    # 倒计时
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    # 打开音频流
    print("开始录制...请说话")
    stream = p.open(format=audio_format,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=chunk)
    
    frames = []
    
    # 录制音频
    for i in range(0, int(sample_rate / chunk * seconds)):
        data = stream.read(chunk)
        frames.append(data)
        # 显示录制进度
        if i % 10 == 0:
            progress = (i / int(sample_rate / chunk * seconds)) * 100
            print(f"录制中... {progress:.1f}%", end="\r")
    
    print("\n录制完成!")
    
    # 关闭音频流
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # 保存音频文件
    wf = wave.open(file_name, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(audio_format))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    print(f"音频已保存至: {os.path.abspath(file_name)}")

def main():
    """主函数"""
    file_name = "input.wav"
    record_seconds = int(input("请输入要录制的秒数（推荐5-10秒）: ") or "5")
    
    record_audio(file_name, record_seconds)
    print(f"\n您可以通过运行 'python voice_assistant.py' 来处理刚录制的问题")

if __name__ == "__main__":
    main()