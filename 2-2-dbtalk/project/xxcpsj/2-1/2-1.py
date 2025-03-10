from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# 创建数据库并创建对话表
def init_db():
    conn = sqlite3.connect('conversations.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_input TEXT NOT NULL,
            model_response TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 存储对话数据的路由
@app.route('/store_message', methods=['POST'])
def store_message():
    try:
        data = request.get_json()
        
        # 获取时间戳，如果ESP32没有提供，则使用服务器时间
        timestamp = data.get('timestamp')
        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        user_input = data.get('user_input')
        model_response = data.get('model_response')

        conn = sqlite3.connect('conversations.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO conversations (timestamp, user_input, model_response)
            VALUES (?, ?, ?)
        ''', (timestamp, user_input, model_response))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Message stored successfully', 'timestamp': timestamp}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 获取所有对话的路由（可选）
@app.route('/get_conversations', methods=['GET'])
def get_conversations():
    try:
        conn = sqlite3.connect('conversations.db')
        conn.row_factory = sqlite3.Row  # 返回字典而不是元组
        c = conn.cursor()
        c.execute('SELECT * FROM conversations ORDER BY id DESC')
        rows = c.fetchall()
        
        conversations = []
        for row in rows:
            conversations.append({
                'id': row['id'],
                'timestamp': row['timestamp'],
                'user_input': row['user_input'],
                'model_response': row['model_response']
            })
            
        conn.close()
        return jsonify({'conversations': conversations}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)