import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, AIAnalysisResult

def update_analysis_results():
    """更新现有的分析结果记录，添加segmentation_image_url字段"""
    with app.app_context():
        # 获取所有分析结果
        results = AIAnalysisResult.query.all()
        
        for result in results:
            if result.segmentation_image_path and not result.segmentation_image_url:
                # 构建URL
                result.segmentation_image_url = f"/api/images/segmentation/{os.path.basename(result.segmentation_image_path)}"
                print(f"更新分析结果 {result.id}: {result.segmentation_image_url}")
        
        # 提交更改
        db.session.commit()
        print(f"已更新 {len(results)} 条记录")

if __name__ == "__main__":
    update_analysis_results() 