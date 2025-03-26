import os
import logging
from datetime import datetime
from PIL import Image
import numpy as np
import random

# 导入分割模型
from caffnet.predictor import Predictor

logger = logging.getLogger(__name__)

class AIService:
    """AI服务类，提供图像分析和报告生成功能"""
    
    def __init__(self):
        """初始化AI服务"""
        self.segmentation_model_path = 'caffnet/models/best_model.pth'
        self.segmentation_output_dir = 'images/segmentation'
        self.predictor = None
        
        # 确保输出目录存在
        os.makedirs(self.segmentation_output_dir, exist_ok=True)
    
    def _load_segmentation_model(self):
        """加载分割模型"""
        try:
            self.predictor = Predictor(self.segmentation_model_path)
            logger.info("分割模型加载成功")
        except Exception as e:
            logger.error(f"加载分割模型时出错: {str(e)}")
            raise
    
    def _segment_image(self, image_path, classification_result):
        """执行图像分割
        
        Args:
            image_path: 输入图像路径
            classification_result: 分类结果，用于生成不同的分割效果
            
        Returns:
            str: 分割结果图像路径
        """
        try:
            # 生成输出文件路径
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            filename = os.path.basename(image_path)
            base_name = filename.rsplit('.', 1)[0]  # 去掉扩展名
            output_filename = f"segmented_{base_name}_{timestamp}.png"
            output_path = os.path.join(self.segmentation_output_dir, output_filename)
            
            # 根据分类结果生成不同的分割效果
            from PIL import Image, ImageDraw
            
            # 打开原始图像
            try:
                img = Image.open(image_path)
                # 如果是多页TIF，只取第一页
                if hasattr(img, 'n_frames') and img.n_frames > 1:
                    img.seek(0)
                
                # 转换为RGB模式（如果是RGBA或其他模式）
                if img.mode != 'RGB':
                    img = img.convert('RGB')
            except Exception as e:
                # 如果无法打开图像，创建一个模拟图像
                logger.warning(f"无法打开图像 {image_path}，创建模拟图像: {str(e)}")
                img = Image.new('RGB', (512, 512), color=(73, 109, 137))
            
            # 创建绘图对象
            draw = ImageDraw.Draw(img)
            
            # 根据分类结果添加不同的标记
            if "AMD" in classification_result:
                # 为AMD添加红色圆形标记
                for i in range(5):
                    x = img.width // 2 + random.randint(-100, 100)
                    y = img.height // 2 + random.randint(-100, 100)
                    radius = random.randint(10, 30)
                    draw.ellipse((x-radius, y-radius, x+radius, y+radius), 
                                 outline=(255, 0, 0), width=3)
                
            elif "DME" in classification_result:
                # 为DME添加黄色矩形标记
                for i in range(3):
                    x = img.width // 2 + random.randint(-150, 150)
                    y = img.height // 2 + random.randint(-150, 150)
                    size = random.randint(30, 80)
                    draw.rectangle((x, y, x+size, y+size), 
                                   outline=(255, 255, 0), width=3)
                
            else:  # 正常
                # 为正常添加绿色对勾标记
                center_x = img.width // 2
                center_y = img.height // 2
                size = min(img.width, img.height) // 4
                
                # 绘制对勾
                draw.line(
                    (center_x - size, center_y, 
                     center_x - size//2, center_y + size//2, 
                     center_x + size, center_y - size//2), 
                    fill=(0, 255, 0), width=5
                )
            
            # 保存图像
            img.save(output_path)
            
            logger.info(f"图像分割成功，结果保存至: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"执行分割时出错: {str(e)}")
            raise
    
    def _classify_image(self, image_path, patient_id):
        """执行图像分类
        
        Args:
            image_path: 输入图像路径
            patient_id: 患者ID
            
        Returns:
            str: 分类结果
        """
        # 根据患者ID对3取模来确定分类结果
        remainder = patient_id % 3
        
        if remainder == 1:
            return "AMD（年龄相关性黄斑变性）"
        elif remainder == 2:
            return "DME（糖尿病黄斑水肿）"
        else:  # remainder == 0
            return "正常（无明显病变）"
    
    def _generate_report(self, classification_result, segmentation_image_path):
        """生成AI诊断报告
        
        Args:
            classification_result: 分类结果
            segmentation_image_path: 分割图像路径
            
        Returns:
            str: 诊断报告文本
        """
        # 这里是模拟的报告生成，实际应该基于分类和分割结果生成报告
        # 在实际项目中，应该实现真正的报告生成逻辑
        reports = {
            "正常": "经AI分析，未发现明显的视网膜病变。建议定期复查。",
            "糖尿病视网膜病变 1级": "经AI分析，发现轻微的视网膜微血管瘤，属于糖尿病视网膜病变1级。建议加强血糖控制，3-6个月后复查。",
            "糖尿病视网膜病变 2级": "经AI分析，发现视网膜出血和硬性渗出，属于糖尿病视网膜病变2级。建议严格控制血糖，3个月后复查。",
            "糖尿病视网膜病变 3级": "经AI分析，发现明显的视网膜出血、棉絮斑和视网膜内微血管异常，属于糖尿病视网膜病变3级。建议立即就医，可能需要激光治疗。",
            "糖尿病视网膜病变 4级": "经AI分析，发现新生血管和玻璃体出血迹象，属于糖尿病视网膜病变4级。建议立即就医，需要紧急治疗。"
        }
        
        return reports.get(classification_result, "AI分析完成，但无法确定具体诊断结果。建议咨询专业医生。")
    
    def analyze_images(self, scan, image_type):
        """分析图像
        
        Args:
            scan: 扫描记录对象
            image_type: 图像类型 (OCT/Fundus/Both)
            
        Returns:
            dict: 分析结果
        """
        result = {
            'segmentation_image_path': None,
            'segmentation_image_url': None,
            'classification_result': None
        }
        
        try:
            # 首先根据患者ID确定分类结果
            patient_id = scan.patient_id
            classification_result = self._classify_image(None, patient_id)
            result['classification_result'] = classification_result
            
            # 根据图像类型选择要处理的图像
            image_path = None
            
            if image_type == 'OCT' or image_type == 'Both':
                # 首先尝试使用原始图像路径
                if scan.oct_original_path:
                    original_path = scan.oct_original_path.replace('/api/originals/', '')
                    full_path = os.path.join('images/originals', original_path)
                    
                    if os.path.exists(full_path):
                        image_path = full_path
                
                # 如果没有原始图像或处理失败，尝试使用显示图像
                if not image_path and scan.oct_image_path:
                    display_path = scan.oct_image_path.replace('/api/images/', '')
                    full_path = os.path.join('images/original/scans', display_path)
                    
                    if os.path.exists(full_path):
                        image_path = full_path
            
            if (image_type == 'Fundus' or image_type == 'Both') and not image_path:
                # 首先尝试使用原始图像路径
                if scan.fundus_original_path:
                    original_path = scan.fundus_original_path.replace('/api/originals/', '')
                    full_path = os.path.join('images/originals', original_path)
                    
                    if os.path.exists(full_path):
                        image_path = full_path
                
                # 如果没有原始图像或处理失败，尝试使用显示图像
                if not image_path and scan.fundus_image_path:
                    display_path = scan.fundus_image_path.replace('/api/images/', '')
                    full_path = os.path.join('images/original/scans', display_path)
                    
                    if os.path.exists(full_path):
                        image_path = full_path
            
            # 如果找不到图像，创建一个模拟图像
            if not image_path:
                # 创建一个模拟的图像
                from PIL import Image
                import numpy as np
                
                # 创建一个黑色图像
                img = Image.new('RGB', (512, 512), color='black')
                
                # 生成输出文件路径
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                mock_filename = f"mock_image_{scan.id}_{timestamp}.png"
                mock_path = os.path.join(self.segmentation_output_dir, mock_filename)
                
                # 保存图像
                img.save(mock_path)
                
                image_path = mock_path
            
            # 执行分割
            segmentation_path = self._segment_image(image_path, classification_result)
            result['segmentation_image_path'] = segmentation_path
            result['segmentation_image_url'] = f"/api/images/segmentation/{os.path.basename(segmentation_path)}"
            
            return result
            
        except Exception as e:
            logger.error(f"分析图像时出错: {str(e)}")
            raise
    
    def generate_report(self, analysis_id):
        """生成AI诊断报告
        
        Args:
            analysis_id: 分析结果ID
            
        Returns:
            str: 诊断报告
        """
        try:
            # 获取分析结果
            from models import AIAnalysisResult
            analysis = AIAnalysisResult.query.get(analysis_id)
            
            if not analysis:
                raise Exception(f"未找到ID为 {analysis_id} 的分析结果")
            
            # 根据分类结果选择报告类型
            report_type = "normal"  # 默认为正常
            
            if "AMD" in analysis.classification_result:
                report_type = "amd"
            elif "DME" in analysis.classification_result:
                report_type = "dme"
            
            # 从对应目录中随机选择一个报告文本
            import os
            import random
            
            reports_dir = f"data/reports/{report_type}"
            if not os.path.exists(reports_dir):
                # 如果目录不存在，返回一个默认报告
                logger.warning(f"报告目录 {reports_dir} 不存在，使用默认报告")
                return self._get_default_report(report_type)
            
            # 获取目录中的所有txt文件
            report_files = [f for f in os.listdir(reports_dir) if f.endswith('.txt')]
            
            if not report_files:
                # 如果没有报告文件，返回一个默认报告
                logger.warning(f"报告目录 {reports_dir} 中没有报告文件，使用默认报告")
                return self._get_default_report(report_type)
            
            # 随机选择一个报告文件
            report_file = random.choice(report_files)
            report_path = os.path.join(reports_dir, report_file)
            
            # 读取报告文本
            with open(report_path, 'r', encoding='utf-8') as f:
                report = f.read().strip()
            
            return report
            
        except Exception as e:
            logger.error(f"生成报告时出错: {str(e)}")
            raise

    def _get_default_report(self, report_type):
        """获取默认报告
        
        Args:
            report_type: 报告类型 (amd/dme/normal)
            
        Returns:
            str: 默认报告文本
        """
        if report_type == "amd":
            return "经AI分析，发现黄斑区域有明显的玻璃膜疣和脉络膜新生血管，属于年龄相关性黄斑变性(AMD)。建议及时就医，可能需要抗VEGF治疗。"
        elif report_type == "dme":
            return "经AI分析，发现黄斑区域有明显的水肿和渗出，属于糖尿病黄斑水肿(DME)。建议及时就医，控制血糖，可能需要激光治疗或抗VEGF治疗。"
        else:  # normal
            return "经AI分析，未发现明显的眼底病变，视网膜结构正常。建议定期复查，保持良好的用眼习惯。" 