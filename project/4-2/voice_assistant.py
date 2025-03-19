#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from datetime import datetime
import time

# 导入我们的模块
from stt_module import recognize_speech
from llm_module import query_llm
from tts_module import text_to_speech

def run_assistant(input_audio="input.wav", output_audio="output.wav"):
    """
    运行语音助手完整流程：
    1. 语音识别(STT)
    2. 大语言模型处理(LLM)
    3. 语音合成(TTS)
    """
    print("=" * 50)
    print("语音助手启动中...")
    print("=" * 50)
    
    # 步骤1: 语音识别
    print("\n[步骤1] 正在进行语音识别...")
    recognized_text = recognize_speech(input_audio)
    
    if not recognized_text:
        print("语音识别失败，无法继续。")
        return False
    
    print(f"识别结果: {recognized_text}")
    
    # 步骤2: 发送到LLM获取回复
    print("\n[步骤2] 正在向大语言模型发送请求...")
    llm_response = query_llm(recognized_text)
    
    if not llm_response:
        print("大语言模型没有返回有效回复，无法继续。")
        return False
    
    print(f"LLM回复: {llm_response}")
    
    # 步骤3: 语音合成
    print("\n[步骤3] 正在将回复转换为语音...")
    tts_result = text_to_speech(llm_response, output_audio)
    
    if not tts_result:
        print("语音合成失败。")
        return False
    
    print("\n处理完成！")
    print(f"输入识别为: {recognized_text}")
    print(f"AI回复: {llm_response}")
    print(f"语音输出文件: {os.path.abspath(output_audio)}")
    
    return True

def main():
    """主函数"""
    # 你可以在这里添加命令行参数的处理
    # 例如: input_file = sys.argv[1] if len(sys.argv) > 1 else "input.wav"
    
    input_file = "output.wav"  # 默认输入文件
    output_file = "ai_response.wav"  # 默认输出文件
    
    print("语音助手 - STT -> LLM -> TTS 流程")
    print(f"预期输入文件: {input_file}")
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"警告: 输入文件 {input_file} 不存在。")
        print("请准备一个包含语音问题的音频文件。")
        return
    
    # 运行助手
    run_assistant(input_file, output_file)

if __name__ == "__main__":
    main()