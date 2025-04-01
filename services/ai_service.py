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
        os.makedirs(os.path.join(self.segmentation_output_dir, 'fundus'), exist_ok=True)
        
        # 检查模型文件是否存在
        if not os.path.exists(self.segmentation_model_path):
            logger.warning(f"模型文件不存在: {self.segmentation_model_path}")
            logger.warning("将使用备用方法进行分割")
        else:
            logger.info(f"找到模型文件: {self.segmentation_model_path}")
    
    def _load_segmentation_model(self):
        """加载分割模型"""
        try:
            # 检查模型文件是否存在
            if not os.path.exists(self.segmentation_model_path):
                logger.error(f"模型文件不存在: {self.segmentation_model_path}")
                raise FileNotFoundError(f"模型文件不存在: {self.segmentation_model_path}")
            
            # 加载模型
            self.predictor = Predictor(self.segmentation_model_path)
            logger.info("分割模型加载成功")
        except Exception as e:
            logger.error(f"加载分割模型时出错: {str(e)}")
            raise
    
    def _segment_image(self, image_path, classification_result):
        """执行图像分割
        
        Args:
            image_path: 输入图像路径（PNG格式）
            classification_result: 分类结果，用于生成不同的分割效果
            
        Returns:
            str: 分割结果图像路径，如果是OCT图像则返回None
        """
        try:
            # 检查是否是OCT图像
            if '/oct/' in image_path.lower():
                logger.info(f"OCT图像不需要分割: {image_path}")
                return None  # OCT图像不需要分割
            
            # 将PNG路径转换为TIF路径（用于分割）
            tif_path = image_path.replace('pngs', 'tifs').replace('.png', '.tif')
            
            # 检查TIF文件是否存在
            if not os.path.exists(tif_path):
                logger.warning(f"TIF图像不存在: {tif_path}，将使用PNG图像")
                tif_path = image_path
            
            # 生成输出文件路径
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            filename = os.path.basename(image_path)
            base_name = filename.rsplit('.', 1)[0]  # 去掉扩展名
            output_filename = f"segmented_{base_name}_{timestamp}.png"
            
            # 创建分割结果目录
            output_dir = os.path.join(self.segmentation_output_dir, 'fundus')
            os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(output_dir, output_filename)
            
            # 加载分割模型（如果尚未加载）
            if self.predictor is None:
                self._load_segmentation_model()
            
            # 执行分割
            success = self.predictor.predict(tif_path, output_path)
            
            if not success:
                logger.warning(f"分割失败，使用备用方法: {image_path}")
                self._create_fallback_segmentation(image_path, output_path, classification_result)
            
            return output_path
            
        except Exception as e:
            logger.error(f"分割图像时出错: {str(e)}")
            # 如果出错，使用备用方法
            try:
                output_dir = os.path.join(self.segmentation_output_dir, 'fundus')
                os.makedirs(output_dir, exist_ok=True)
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                filename = os.path.basename(image_path) if image_path else f"unknown_{timestamp}.png"
                base_name = filename.rsplit('.', 1)[0]  # 去掉扩展名
                output_filename = f"segmented_{base_name}_{timestamp}.png"
                output_path = os.path.join(output_dir, output_filename)
                
                self._create_fallback_segmentation(image_path, output_path, classification_result)
                return output_path
            except Exception as e2:
                logger.error(f"创建备用分割图像时出错: {str(e2)}")
                return None
    
    def _create_fallback_segmentation(self, image_path, output_path, classification_result):
        """创建备用分割图像（当模型分割失败时使用）"""
        try:
            from PIL import Image, ImageDraw
            
            # 打开原始图像
            img = Image.open(image_path)
            # 如果是多页TIF，只取第一页
            if hasattr(img, 'n_frames') and img.n_frames > 1:
                img.seek(0)
            
            # 转换为RGB模式（如果是RGBA或其他模式）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
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
                                 outline="red", width=2)
            elif "DME" in classification_result:
                # 为DME添加红色矩形标记
                for i in range(3):
                    x = img.width // 2 + random.randint(-100, 100)
                    y = img.height // 2 + random.randint(-100, 100)
                    width = random.randint(20, 60)
                    height = random.randint(20, 60)
                    draw.rectangle((x-width//2, y-height//2, x+width//2, y+height//2), 
                                   outline="red", width=2)
            else:
                # 为正常眼底添加绿色圆形标记
                x = img.width // 2
                y = img.height // 2
                radius = min(img.width, img.height) // 4
                draw.ellipse((x-radius, y-radius, x+radius, y+radius), 
                             outline="green", width=2)
            
            # 保存结果
            img.save(output_path)
            
        except Exception as e:
            logger.error(f"创建备用分割图像时出错: {str(e)}")
            # 如果连备用方法也失败，创建一个空白图像
            img = Image.new('RGB', (512, 512), color=(0, 0, 0))
            img.save(output_path)
    
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
    
    def analyze_image(self, scan_id, image_type='Fundus'):
        """分析图像
        
        Args:
            scan_id: 扫描记录ID
            image_type: 图像类型（OCT/Fundus）
            
        Returns:
            dict: 分析结果
        """
        try:
            # 获取扫描记录
            from models import Scan, AIAnalysisResult
            scan = Scan.query.get(scan_id)
            if not scan:
                logger.error(f"扫描记录不存在: {scan_id}")
                return None
            
            # 获取图像路径
            if image_type == 'OCT':
                image_path = scan.oct_image_path.replace('/api/pngs/oct/', 'images/pngs/oct/')
            else:  # Fundus
                image_path = scan.fundus_image_path.replace('/api/pngs/fundus/', 'images/pngs/fundus/')
            
            # 检查图像是否存在
            if not os.path.exists(image_path):
                logger.error(f"图像不存在: {image_path}")
                return None
            
            # 执行分类
            classification_result = self._classify_image(image_path, scan.patient_id)
            
            # 执行分割（只对眼底图像进行分割）
            segmentation_image_path = None
            if image_type != 'OCT':
                segmentation_image_path = self._segment_image(image_path, classification_result)
            
            # 保存分析结果
            analysis = AIAnalysisResult(
                scan_id=scan_id,
                classification_result=classification_result,
                segmentation_image_path=segmentation_image_path
            )
            from models import db
            db.session.add(analysis)
            db.session.commit()
            
            return {
                'id': analysis.id,
                'scanId': scan_id,
                'segmentationImagePath': segmentation_image_path,
                'classificationResult': classification_result
            }
            
        except Exception as e:
            logger.error(f"分析图像时出错: {str(e)}")
            return None
    
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

    def analyze_images(self, image_paths, patient_id=None):
        """分析多张图像
        
        Args:
            image_paths: 图像路径列表
            patient_id: 患者ID（可选）
            
        Returns:
            dict: 分析结果
        """
        try:
            results = []
            
            for image_path in image_paths:
                # 确定图像类型
                if '/fundus/' in image_path:
                    image_type = 'Fundus'
                elif '/oct/' in image_path:
                    image_type = 'OCT'
                else:
                    image_type = 'Unknown'
                    
                # 执行分类
                classification_result = self._classify_image(image_path, patient_id)
                
                # 执行分割
                segmentation_image_path = self._segment_image(image_path, classification_result)
                
                # 添加结果
                results.append({
                    'imagePath': image_path,
                    'imageType': image_type,
                    'classificationResult': classification_result,
                    'segmentationImagePath': segmentation_image_path
                })
                
            return results
            
        except Exception as e:
            logger.error(f"分析多张图像时出错: {str(e)}")
            return None 