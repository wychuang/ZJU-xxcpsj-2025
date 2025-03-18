from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# 创建数据库并创建对话表
def init_db():
    conn = sqlite3.connect('conversations.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    data = request.get_json()
    user_input = data.get('user_input')
    model_response = data.get('model_response')

    conn = sqlite3.connect('conversations.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO conversations (user_input, model_response)
        VALUES (?, ?)
    ''', (user_input, model_response))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Message stored successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
