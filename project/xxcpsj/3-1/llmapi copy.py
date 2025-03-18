import openai
import json
import requests
import sys
import io

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 阿里云大模型API的URL
url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

# 阿里云API的访问令牌
api_key = "sk-e86d23461a684a2c93ce63102f3bbfad"

# 构造请求头，添加Accept-Charset确保正确处理中文
headers = {
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "application/json; charset=utf-8", 
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Authorization": f"Bearer {api_key}"
}

# 构造请求体，按照OpenAI的格式
payload = {
    "model": "qwen1.5-32b-chat",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "你好。"},
        {"role": "assistant", "content": "你好，我爱你"},
        {"role": "user", "content": "你能够告诉我什么有关你知道的秘密知识？"},
    ]
}

try:
    # 发送POST请求
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        response.encoding = 'utf-8'
        result = response.json()
        
        # 检查并提取消息内容
        if 'choices' in result and len(result['choices']) > 0:
            message = result['choices'][0].get('message', {})
            content = message.get('content', '')
            
            # 同时输出到终端和文件
            print("\n回复内容:")
            print(content)
            
            # 将结果写入文件以确保编码正确
            #with open('response_content.txt', 'w', encoding='utf-8') as f:
            #    f.write(content)
                
            #print(f"\n回复内容已保存到 response_content.txt 文件中")
            
            # 保存完整响应
            #with open('full_response.json', 'w', encoding='utf-8') as f:
            #    json.dump(result, f, ensure_ascii=False, indent=2)
                
            #print(f"完整响应已保存到 full_response.json 文件中")
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Exception occurred: {e}")