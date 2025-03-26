import sys
import os
import random
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Scan, AIAnalysisResult, Patient
from sqlalchemy import text

# 各种分类的描述模板
normal_descriptions = [
    "经AI分析，眼底图像未见明显病变，视网膜血管清晰，黄斑区结构完整，OCT图像显示视网膜厚度正常，未见异常信号。目前眼部状况良好，建议保持良好的用眼习惯，定期进行眼科检查，以早期发现潜在问题。",
    "AI分析结果显示，眼底图像正常，无明显病变。视网膜血管走行规则，无出血或渗出。OCT扫描显示视网膜各层结构清晰，黄斑中心凹形态正常。建议定期复查，保持健康生活方式。",
    "根据AI分析，患者眼底检查正常。视盘形态正常，边界清晰，C/D比值在正常范围内。视网膜无出血、渗出或微血管瘤。OCT显示视网膜层次结构完整，无水肿或萎缩。建议继续保持良好用眼习惯。",
    "AI系统分析显示正常眼底状态。视网膜血管分布均匀，动静脉比例正常。黄斑区反光正常，无色素异常。OCT检查显示视网膜厚度在正常范围内，各层结构清晰可辨。无需特殊治疗，建议定期随访。",
    "AI辅助诊断结果为正常。眼底图像显示视盘色泽正常，边界清晰；黄斑区无异常；视网膜血管走行正常，无狭窄或扩张。OCT显示视网膜层次结构完整，无异常信号。建议保持良好生活习惯，避免长时间用眼疲劳。"
]

dme_descriptions = [
    "AI分析结果提示糖尿病黄斑水肿(DME)。OCT图像显示黄斑区视网膜增厚，内层视网膜出现囊样水肿腔，视网膜下可见硬性渗出。眼底照相显示黄斑区有微血管瘤和出血点。建议及时进行抗VEGF治疗或激光光凝治疗，同时加强血糖控制。",
    "根据AI分析，患者眼底表现符合糖尿病黄斑水肿(DME)。OCT显示黄斑中心凹视网膜增厚，测量厚度超过正常值，可见多发囊腔。眼底可见散在出血点和硬性渗出。建议转诊视网膜专科医生进行进一步评估和治疗。",
    "AI辅助诊断显示糖尿病黄斑水肿(DME)特征。黄斑区视网膜明显增厚，OCT显示视网膜内多个低反射囊腔，视网膜层结构紊乱。眼底照相可见黄斑区环形硬性渗出。建议进行抗VEGF玻璃体腔注射治疗，并严格控制血糖、血压和血脂。",
    "AI系统检测到糖尿病黄斑水肿(DME)。OCT图像显示黄斑区视网膜不规则增厚，内层和外层均可见囊样腔隙，视网膜下液体积聚。眼底照相显示黄斑区出血点和硬性渗出。建议尽快进行眼科治疗，同时加强全身代谢控制。",
    "AI分析结果高度提示糖尿病黄斑水肿(DME)。OCT显示黄斑中心凹视网膜厚度增加，内层视网膜出现多发囊腔，外层视网膜结构紊乱。眼底可见散在微血管瘤和硬性渗出。建议进行抗VEGF治疗，并密切监测血糖水平。"
]

amd_descriptions = [
    "AI分析结果提示年龄相关性黄斑变性(AMD)。OCT图像显示视网膜色素上皮层不规则，可见玻璃膜疣形成，黄斑区视网膜变薄。眼底照相显示黄斑区有多发玻璃膜疣和色素紊乱。建议服用AREDS配方营养补充剂，避免吸烟，定期复查。",
    "根据AI分析，患者眼底表现符合年龄相关性黄斑变性(AMD)。OCT显示视网膜色素上皮不规则隆起，黄斑区可见玻璃膜疣和地图状萎缩。眼底可见黄斑区色素紊乱和玻璃膜疣。建议转诊视网膜专科医生进行进一步评估和治疗。",
    "AI辅助诊断显示年龄相关性黄斑变性(AMD)特征。OCT显示视网膜色素上皮层不规则，黄斑区可见多发玻璃膜疣，部分区域视网膜色素上皮萎缩。眼底照相可见黄斑区色素紊乱。建议避免吸烟，保护眼睛避免强光照射，服用抗氧化营养补充剂。",
    "AI系统检测到年龄相关性黄斑变性(AMD)。OCT图像显示视网膜色素上皮层不规则，黄斑区可见玻璃膜疣形成，部分区域视网膜变薄。眼底照相显示黄斑区色素紊乱和玻璃膜疣。建议定期复查，监测病情进展，必要时考虑抗VEGF治疗。",
    "AI分析结果高度提示年龄相关性黄斑变性(AMD)。OCT显示视网膜色素上皮不规则，黄斑区可见多发玻璃膜疣，部分区域视网膜色素上皮萎缩。眼底可见黄斑区色素紊乱和玻璃膜疣。建议定期复查，避免吸烟，保护眼睛避免强光照射。"
]

def update_ai_analysis_results():
    """更新AI分析结果，按照患者ID对3取模的规则设置分类"""
    with app.app_context():
        try:
            print("开始更新AI分析结果...")
            
            # 获取所有扫描记录
            scans = Scan.query.all()
            
            # 更新每个扫描记录对应的AI分析结果
            for scan in scans:
                # 获取患者ID
                patient_id = scan.patient_id
                
                # 根据患者ID确定分类
                if patient_id % 3 == 0:
                    classification = "正常（无明显病变）"
                    description = random.choice(normal_descriptions)
                elif patient_id % 3 == 1:
                    classification = "DME（糖尿病黄斑水肿）"
                    description = random.choice(dme_descriptions)
                else:  # patient_id % 3 == 2
                    classification = "AMD（年龄相关性黄斑变性）"
                    description = random.choice(amd_descriptions)
                
                # 查找该扫描记录对应的AI分析结果
                analysis_result = AIAnalysisResult.query.filter_by(scan_id=scan.id).first()
                
                if analysis_result:
                    # 更新现有记录
                    analysis_result.classification_result = classification
                    analysis_result.report = description
                else:
                    # 创建新记录
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    segmentation_image_name = f"segmented_{scan.id}_{timestamp}.png"
                    segmentation_image_path = f"images/segmentation/{segmentation_image_name}"
                    
                    analysis_result = AIAnalysisResult(
                        scan_id=scan.id,
                        segmentation_image_path=segmentation_image_path,
                        classification_result=classification,
                        report=description
                    )
                    db.session.add(analysis_result)
            
            db.session.commit()
            print("AI分析结果更新完成!")
            
        except Exception as e:
            print(f"更新AI分析结果时出错: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    update_ai_analysis_results() 