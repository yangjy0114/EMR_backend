import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mysql import connector
from scripts.create_database import create_database
from scripts.init_db import init_database
from scripts.create_test_data import create_test_data

def reset_database():
    """重置数据库"""
    try:
        # 连接MySQL（不指定数据库）
        cnx = connector.connect(
            host='test-db-mysql.ns-32fwr7d7.svc',
            user='root',
            password='59fh8r22'
        )
        
        cursor = cnx.cursor()
        
        # 删除数据库（如果存在）
        try:
            cursor.execute("DROP DATABASE IF EXISTS `test_db`")
            print("已删除旧数据库")
        except Exception as e:
            print(f"删除数据库时出错: {str(e)}")
            
        cursor.close()
        cnx.close()
        
        # 重新创建数据库和表
        print("\n开始重新创建数据库...")
        create_database()
        
        print("\n开始创建表...")
        init_database()
        
        print("\n开始创建测试数据...")
        create_test_data()
        
        print("\n数据库重置完成！")
        
    except Exception as e:
        print(f"重置数据库时出错: {str(e)}")

if __name__ == "__main__":
    reset_database() 