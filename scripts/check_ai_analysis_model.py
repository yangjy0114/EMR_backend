import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import AIAnalysisResult

def check_ai_analysis_model():
    """检查AIAnalysisResult模型的字段"""
    with app.app_context():
        # 打印AIAnalysisResult模型的所有列
        for column in AIAnalysisResult.__table__.columns:
            print(f"列名: {column.name}, 类型: {column.type}")

if __name__ == "__main__":
    check_ai_analysis_model() 