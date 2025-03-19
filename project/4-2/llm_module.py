import requests
import json

def query_llm(user_input):
    """
    Send query to Alibaba Cloud LLM and get response
    
    Args:
        user_input (str): User's text input to send to the LLM
    
    Returns:
        str: The LLM's response text or error message
    """
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
    
    # 构造请求体，按照OpenAI的格式
    payload = {
        "model": "qwen1.5-32b-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input}
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
                return content
            else:
                return "解析响应失败: " + json.dumps(result, ensure_ascii=False)
        else:
            return f"请求错误: {response.status_code}, {response.text}"
    except Exception as e:
        return f"发生异常: {e}"