import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db
from sqlalchemy import text

def add_report_field():
    """添加report字段到ai_analysis_results表"""
    with app.app_context():
        try:
            print("添加report字段到ai_analysis_results表...")
            
            # 检查字段是否已存在
            result = db.session.execute(text("SHOW COLUMNS FROM ai_analysis_results LIKE 'report'"))
            if result.fetchone():
                print("report字段已存在")
                return
            
            # 添加字段
            db.session.execute(text("ALTER TABLE ai_analysis_results ADD COLUMN report TEXT"))
            db.session.commit()
            
            print("report字段添加成功!")
            
        except Exception as e:
            print(f"添加字段时出错: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    add_report_field() 