import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db

def create_table_without_fk():
    """创建不带外键约束的ai_analysis_results表"""
    with app.app_context():
        try:
            # 使用text()函数包装SQL语句
            from sqlalchemy import text
            
            # 删除表
            db.session.execute(text("DROP TABLE IF EXISTS ai_analysis_results"))
            db.session.commit()
            print("成功删除ai_analysis_results表")
            
            # 创建表
            create_table_sql = """
            CREATE TABLE ai_analysis_results (
                id BIGINT NOT NULL AUTO_INCREMENT,
                scan_id BIGINT NOT NULL,
                segmentation_image_path VARCHAR(255),
                classification_result VARCHAR(100),
                created_at DATETIME,
                PRIMARY KEY (id)
            )
            """
            db.session.execute(text(create_table_sql))
            db.session.commit()
            print("成功创建ai_analysis_results表")
                
        except Exception as e:
            print(f"创建表时出错: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    create_table_without_fk() 