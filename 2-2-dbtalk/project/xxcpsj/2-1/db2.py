import sqlite3

def update_database():
    print("正在更新数据库结构...")
    conn = sqlite3.connect('conversations.db')
    c = conn.cursor()
    
    # 检查timestamp列是否存在
    c.execute("PRAGMA table_info(conversations)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]
    
    if "timestamp" not in column_names:
        print("添加timestamp列...")
        try:
            c.execute("ALTER TABLE conversations ADD COLUMN timestamp TEXT")
            conn.commit()
            print("数据库更新成功！")
        except sqlite3.Error as e:
            print(f"数据库更新错误: {e}")
    else:
        print("timestamp列已存在")
    
    conn.close()

if __name__ == "__main__":
    update_database()