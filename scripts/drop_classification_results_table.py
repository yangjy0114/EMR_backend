import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db
from sqlalchemy import text

def drop_classification_results_table():
    """删除classification_results表"""
    with app.app_context():
        try:
            # 检查表是否存在
            result = db.session.execute(text("SHOW TABLES LIKE 'classification_results'"))
            if result.fetchone():
                # 删除表
                db.session.execute(text("DROP TABLE classification_results"))
                db.session.commit()
                print("成功删除classification_results表")
            else:
                print("classification_results表不存在")
                
        except Exception as e:
            print(f"删除表时出错: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    drop_classification_results_table() 