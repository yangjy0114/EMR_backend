import os
from datetime import datetime
import logging

# 不需要修改 sys.path
from caffnet.predictor import Predictor  # 使用绝对导入

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SegmentationService:
    def __init__(self, model_path, output_dir):
        """初始化分割服务
        
        Args:
            model_path: 预训练模型路径
            output_dir: 分割结果保存目录
        """
        self.model_path = model_path
        self.output_dir = output_dir
        self.predictor = None
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
    def load_model(self):
        """加载预训练模型"""
        try:
            # 添加 caffnet 目录到 Python 路径
            sys.path.append('caffnet')
            from predictor import Predictor
            
            self.predictor = Predictor(self.model_path)
            logger.info("预测器初始化成功")
            
        except Exception as e:
            logger.error(f"加载模型时出错: {str(e)}")
            raise
            
    def segment_image(self, image_path):
        """执行图像分割
        
        Args:
            image_path: 输入图像路径
            
        Returns:
            str: 分割结果图像路径
        """
        try:
            if self.predictor is None:
                self.load_model()
                
            # 生成输出文件路径
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            filename = os.path.basename(image_path)
            output_filename = f"segmented_{filename.rsplit('.', 1)[0]}_{timestamp}.png"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # 执行分割
            success = self.predictor.predict(image_path, output_path)
            
            if success:
                logger.info(f"图像分割成功，结果保存至: {output_path}")
                return output_path
            else:
                raise Exception("图像分割失败")
                
        except Exception as e:
            logger.error(f"执行分割时出错: {str(e)}")
            raise 