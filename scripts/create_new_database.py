import sys
import os
import mysql.connector
from mysql.connector import Error

def create_new_database():
    """创建新的数据库"""
    try:
        # 使用提供的数据库连接信息
        host = "test-db-mysql.ns-32fwr7d7.svc"
        user = "root"
        password = "59fh8r22"
        port = 3306
        new_db_name = "emr_system"
        
        print(f"正在连接到数据库服务器: {host}:{port}")
        
        # 连接到MySQL服务器
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            port=port
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            print("成功连接到MySQL服务器")
            
            # 检查数据库是否已存在
            cursor.execute(f"SHOW DATABASES LIKE '{new_db_name}'")
            result = cursor.fetchone()
            
            if result:
                print(f"数据库 {new_db_name} 已存在，正在删除...")
                cursor.execute(f"DROP DATABASE {new_db_name}")
                print(f"数据库 {new_db_name} 已删除")
            
            # 创建新数据库
            cursor.execute(f"CREATE DATABASE {new_db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"数据库 {new_db_name} 创建成功")
            
            # 创建或更新配置文件
            config_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(config_dir, '.env')
            
            with open(config_path, 'w') as f:
                f.write(f"DB_HOST={host}\n")
                f.write(f"DB_USER={user}\n")
                f.write(f"DB_PASSWORD={password}\n")
                f.write(f"DB_NAME={new_db_name}\n")
                f.write(f"DB_PORT={port}\n")
            
            print(f"配置文件已更新: {config_path}")
            return True
            
    except Error as e:
        print(f"创建数据库时出错: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL连接已关闭")

if __name__ == "__main__":
    if create_new_database():
        print("数据库创建成功，请继续执行下一步")
    else:
        print("数据库创建失败，请检查错误并重试") 