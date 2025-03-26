import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db

def update_database():
    """更新数据库，添加AI分析结果表"""
    with app.app_context():
        # 创建AI分析结果表
        db.create_all()
        print("数据库更新成功！")

if __name__ == "__main__":
    update_database() 