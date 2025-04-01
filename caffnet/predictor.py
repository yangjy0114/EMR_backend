import os
import time
import torch
from torchvision import transforms
import numpy as np
from PIL import Image
import logging

# 不需要修改 sys.path
from .src.caffnet import CaFFNet  # 使用相对导入

logger = logging.getLogger(__name__)

class Predictor:
    def __init__(self, weights_path):
        """初始化预测器
        
        Args:
            weights_path: 模型权重文件路径
        """
        self.weights_path = weights_path
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.mean = (0.709, 0.381, 0.224)
        self.std = (0.127, 0.079, 0.043)
        self.classes = 1  # exclude background
        self.model = None
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=self.mean, std=self.std)
        ])
        
        # 加载模型
        self._load_model()
        
    def _load_model(self):
        """加载模型"""
        try:
            self.model = CaFFNet(in_channels=3, num_classes=self.classes + 1, base_c=16)
            state_dict = torch.load(self.weights_path, map_location='cpu', weights_only=False)
            self.model.load_state_dict(state_dict['model'])
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"模型加载成功，使用设备: {self.device}")
        except Exception as e:
            logger.error(f"加载模型失败: {str(e)}")
            raise
            
    def predict(self, input_path, output_path):
        """执行图像分割预测
        
        Args:
            input_path: 输入图像路径
            output_path: 输出图像保存路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 只创建输出目录
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 加载图像
            original_img = Image.open(input_path).convert('RGB')
            
            # 预处理
            img = self.transform(original_img)
            img = torch.unsqueeze(img, dim=0)
            
            with torch.no_grad():
                # 初始化模型
                img_height, img_width = img.shape[-2:]
                init_img = torch.zeros((1, 3, img_height, img_width), device=self.device)
                self.model(init_img)
                
                # 执行预测
                output = self.model(img.to(self.device))
                prediction = output['out'].argmax(1).squeeze(0)
                prediction = prediction.to("cpu").numpy().astype(np.uint8)
                
                # 后处理
                prediction[prediction == 1] = 255
                
                # 保存结果
                mask = Image.fromarray(prediction)
                mask.save(output_path)
                
                logger.info(f"分割完成，结果已保存到: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"预测过程出错: {str(e)}")
            return False 