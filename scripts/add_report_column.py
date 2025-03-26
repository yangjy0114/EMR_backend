import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db

def add_report_column():
    """手动添加report字段到ai_analysis_results表"""
    with app.app_context():
        try:
            # 使用text()函数包装SQL语句
            from sqlalchemy import text
            
            # 检查字段是否已存在
            result = db.session.execute(text("SHOW COLUMNS FROM ai_analysis_results LIKE 'report'"))
            columns = result.fetchall()
            
            if not columns:
                # 添加字段
                db.session.execute(text("ALTER TABLE ai_analysis_results ADD COLUMN report TEXT"))
                db.session.commit()
                print("成功添加report字段到ai_analysis_results表")
            else:
                print("report字段已存在")
                
        except Exception as e:
            print(f"添加字段时出错: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    add_report_column() 