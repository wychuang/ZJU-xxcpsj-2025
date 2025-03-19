#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import subprocess
import json
from datetime import datetime

def record_audio_windows(output_file="input.wav", duration=5):
    """
    使用Windows PowerShell命令录制音频
    参数:
        output_file: 输出音频文件路径
        duration: 录音时长(秒)
    返回:
        是否成功
    """
    print(f"准备录音 {duration} 秒...")
    print("3秒后开始录音,请准备好您的问题...")
    
    # 倒计时
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    print("开始录音...请说话")
    
    # 使用PowerShell命令录制音频
    ps_command = f"""
    Add-Type -AssemblyName System.Speech;
    $recognizer = New-Object System.Speech.Recognition.SpeechRecognizer;
    $audio = New-Object System.IO.MemoryStream;
    $recognizer.AudioState = [System.Speech.Recognition.AudioState]::Stopped;
    Start-Sleep -s 0.5;
    $recognizer.AudioState = [System.Speech.Recognition.AudioState]::Silence;
    Start-Sleep -s {duration};
    $recognizer.AudioState = [System.Speech.Recognition.AudioState]::Stopped;
    $wave = $recognizer.AudioFormat.GetWaveFormatBytes();
    [System.IO.File]::WriteAllBytes('{os.path.abspath(output_file)}', $wave + $audio.ToArray());
    """
    
    try:
        subprocess.run(["powershell", "-Command", ps_command], check=True)
        print("录音完成!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"录音失败: {e}")
        return False

def play_audio_windows(audio_file):
    """
    使用Windows内置命令播放音频
    参数:
        audio_file: 音频文件路径
    """
    if not os.path.exists(audio_file):
        print(f"错误: 文件 {audio_file} 不存在")
        return False
    
    print(f"播放音频: {audio_file}")
    
    try:
        # 使用PowerShell命令播放音频
        ps_command = f"""
        Add-Type -AssemblyName System.Speech;
        $player = New-Object System.Media.SoundPlayer;
        $player.SoundLocation = '{os.path.abspath(audio_file)}';
        $player.PlaySync();
        """
        subprocess.run(["powershell", "-Command", ps_command], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"播放失败: {e}")
        return False

def run_stt(audio_file):
    """
    使用simple-stt.py进行语音识别
    参数:
        audio_file: 待识别的音频文件路径
    返回:
        识别出的文本
    """
    print(f"正在识别音频文件: {audio_file}")
    # 使用subprocess调用您的STT脚本
    result = subprocess.run(['python', 'simple-stt.py', audio_file], 
                            capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode != 0:
        print(f"STT处理失败: {result.stderr}")
        return None
    
    # 从输出中提取识别结果
    output_lines = result.stdout.split('\n')
    for line in output_lines:
        if "最终识别结果:" in line:
            return line.split("最终识别结果:")[1].strip()
    
    return None

def query_llm(user_input):
    """
    发送查询到阿里云大语言模型并获取响应
    参数:
        user_input: 用户的文本输入
    返回:
        模型的文本回复
    """
    # 导入自定义的LLM模块
    try:
        from llm_module import query_llm as llm_query
        return llm_query(user_input)
    except ImportError:
        print("无法导入llm_module,使用内置实现替代")
    
    # 阿里云大模型API的URL
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    
    # 阿里云API的访问令牌
    api_key = "sk-e86d23461a684a2c93ce63102f3bbfad"
    
    # 构造请求头
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json; charset=utf-8", 
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 构造请求体
    payload = {
        "model": "qwen1.5-32b-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input}
        ]
    }
    
    try:
        # 发送POST请求
        import requests
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            response.encoding = 'utf-8'
            result = response.json()
            
            # 检查并提取消息内容
            if 'choices' in result and len(result['choices']) > 0:
                message = result['choices'][0].get('message', {})
                content = message.get('content', '')
                return content
            else:
                return "解析响应失败"
        else:
            return f"请求错误: {response.status_code}"
    except Exception as e:
        return f"发生异常: {e}"

def run_tts(text, output_file="output.wav"):
    """
    使用simple-tts.py进行语音合成
    参数:
        text: 要合成的文本
        output_file: 输出音频文件路径
    返回:
        是否成功
    """
    print(f"正在合成文本: {text}")
    # 创建临时文本文件
    with open("tts_temp.txt", "w", encoding="utf-8") as f:
        f.write(text)
    
    # 使用subprocess调用您的TTS脚本
    result = subprocess.run(['python', 'simple-tts.py', 'tts_temp.txt', output_file], 
                            capture_output=True, text=True, encoding='utf-8')
    
    # 清理临时文件
    if os.path.exists("tts_temp.txt"):
        os.remove("tts_temp.txt")
    
    if result.returncode != 0:
        print(f"TTS处理失败: {result.stderr}")
        return False
    
    return True

def process_full_auto(duration=5, input_file="input.wav", output_file="ai_response.wav"):
    """
    完整自动化流程:
    1. 录音
    2. 语音识别(STT)
    3. 大语言模型(LLM)
    4. 语音合成(TTS)
    5. 播放结果
    """
    print("=" * 60)
    print("全自动语音交互助手启动")
    print("=" * 60)
    
    # 步骤1: 录音
    print("\n[步骤1] 开始录音...")
    if not record_audio_windows(input_file, duration):
        print("录音失败,无法继续")
        return False
    
    # 步骤2: 语音识别
    print("\n[步骤2] 正在进行语音识别...")
    start_time = datetime.now()
    recognized_text = run_stt(input_file)
    end_time = datetime.now()
    
    if not recognized_text:
        print("语音识别失败,无法继续.")
        return False
    
    print(f"识别结果: {recognized_text}")
    print(f"识别耗时: {end_time - start_time}")
    
    # 步骤3: 调用LLM
    print("\n[步骤3] 正在向大语言模型发送请求...")
    start_time = datetime.now()
    llm_response = query_llm(recognized_text)
    end_time = datetime.当前()
    
    if not llm_response:
        print("大语言模型未返回有效响应,无法继续.")
        return False
    
    print(f"LLM回复: {llm_response}")
    print(f"LLM耗时: {end_time - start_time}")
    
    # 步骤4: 语音合成
    print("\n[步骤4] 正在将回复转换为语音...")
    start_time = datetime.当前()
    tts_success = run_tts(llm_response, output_file)
    end_time = datetime.当前()
    
    if not tts_success:
        print("语音合成失败.")
        return False
    
    print(f"语音合成耗时: {end_time - start_time}")
    
    # 步骤5: 播放回复
    print("\n[步骤5] 播放AI回复...")
    play_success = play_audio_windows(output_file)
    
    if not play_success:
        print("音频播放失败.")
        return False
    
    print("\n处理完成！")
    print(f"您的问题: {recognized_text}")
    print(f"AI回复: {llm_response}")
    
    return True

def main():
    """主函数"""
    print("全自动语音交互助手")
    print("1. 按回车开始录制语音问题")
    print("2. 系统将自动处理并播放回复")
    
    input("准备好了吗？按回车开始...")
    
    # 获取录音时长
    duration = input("请输入录音时长(秒),默认为5秒: ").strip()
    try:
        duration = int(duration) if duration else 5
    except ValueError:
        print("输入无效,使用默认值5秒")
        duration = 5
    
    # 启动全自动流程
    process_full_auto(duration)
    
    # 询问是否继续
    while input("\n是否继续对话？(y/n): ").lower().strip() in ['y', 'yes', '']:
        process_full_auto(duration)
    
    print("感谢使用全自动语音交互助手！")

if __name__ == "__main__":
    main()