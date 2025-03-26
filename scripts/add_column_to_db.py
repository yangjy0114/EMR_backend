import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db

def add_column_to_db():
    """手动添加segmentation_image_url字段到ai_analysis_results表"""
    with app.app_context():
        try:
            # 检查字段是否已存在
            db.session.execute("SHOW COLUMNS FROM ai_analysis_results LIKE 'segmentation_image_url'")
            result = db.session.fetchall()
            
            if not result:
                # 添加字段
                db.session.execute("ALTER TABLE ai_analysis_results ADD COLUMN segmentation_image_url VARCHAR(255)")
                db.session.commit()
                print("成功添加segmentation_image_url字段到ai_analysis_results表")
            else:
                print("segmentation_image_url字段已存在")
                
        except Exception as e:
            print(f"添加字段时出错: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    add_column_to_db() 