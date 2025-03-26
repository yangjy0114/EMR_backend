import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, AIAnalysisResult

def recreate_ai_analysis_table():
    """重新创建ai_analysis_results表"""
    with app.app_context():
        try:
            # 使用text()函数包装SQL语句
            from sqlalchemy import text
            
            # 删除表
            db.session.execute(text("DROP TABLE IF EXISTS ai_analysis_results"))
            db.session.commit()
            print("成功删除ai_analysis_results表")
            
            # 创建表
            db.metadata.create_all(db.engine, tables=[AIAnalysisResult.__table__])
            print("成功创建ai_analysis_results表")
                
        except Exception as e:
            print(f"重新创建表时出错: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    recreate_ai_analysis_table() 