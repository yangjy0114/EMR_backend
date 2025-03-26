import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db

def check_scans_table():
    """检查scans表的id字段类型"""
    with app.app_context():
        try:
            # 使用text()函数包装SQL语句
            from sqlalchemy import text
            
            # 查询scans表的id字段类型
            result = db.session.execute(text("SHOW COLUMNS FROM scans WHERE Field = 'id'"))
            columns = result.fetchall()
            
            if columns:
                print(f"scans表的id字段类型: {columns[0][1]}")
            else:
                print("未找到scans表的id字段")
                
        except Exception as e:
            print(f"查询表结构时出错: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    check_scans_table() 