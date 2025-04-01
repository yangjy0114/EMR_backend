import os
import sys
import logging
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入必要的模块
from app import app, db
from models import Scan, Patient, PatientScanMapping

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_patient_scan_relations():
    """更新患者与扫描记录的关系"""
    try:
        with app.app_context():
            # 1. 首先清空现有的映射表
            logger.info("清空现有的映射表...")
            PatientScanMapping.query.delete()
            db.session.commit()
            
            # 2. 定义患者与扫描记录的映射关系
            patient_scan_mapping = {
                1: [1, 2, 3, 4],      # 患者1的扫描记录
                2: [5, 6, 7],         # 患者2的扫描记录
                3: [8],               # 患者3的扫描记录
                4: [9],               # 患者4的扫描记录
                5: [10],              # 患者5的扫描记录
                6: [11],              # 患者6的扫描记录
                7: [12],              # 患者7的扫描记录
                8: [13],              # 患者8的扫描记录
                9: [14],              # 患者9的扫描记录
                10: [15]              # 患者10的扫描记录
            }
            
            # 3. 更新scans表中的patient_id字段
            logger.info("更新scans表中的patient_id字段...")
            for patient_id, scan_ids in patient_scan_mapping.items():
                for scan_id in scan_ids:
                    scan = Scan.query.get(scan_id)
                    if scan:
                        scan.patient_id = patient_id
                        logger.info(f"更新扫描记录: scan_id={scan_id}, patient_id={patient_id}")
                    else:
                        logger.warning(f"扫描记录不存在: scan_id={scan_id}")
            
            db.session.commit()
            
            # 4. 创建映射记录
            logger.info("创建映射记录...")
            for patient_id, scan_ids in patient_scan_mapping.items():
                # 检查患者是否存在
                patient = Patient.query.get(patient_id)
                if not patient:
                    logger.warning(f"患者不存在: patient_id={patient_id}")
                    continue
                
                for scan_id in scan_ids:
                    # 检查扫描记录是否存在
                    scan = Scan.query.get(scan_id)
                    if not scan:
                        logger.warning(f"扫描记录不存在: scan_id={scan_id}")
                        continue
                    
                    # 创建映射记录
                    mapping = PatientScanMapping(patient_id=patient_id, scan_id=scan_id)
                    db.session.add(mapping)
                    logger.info(f"创建映射记录: patient_id={patient_id}, scan_id={scan_id}")
            
            db.session.commit()
            logger.info("患者与扫描记录的关系更新完成！")
            
            # 5. 验证更新结果
            logger.info("验证更新结果...")
            for patient_id, scan_ids in patient_scan_mapping.items():
                mappings = PatientScanMapping.query.filter_by(patient_id=patient_id).all()
                logger.info(f"患者 {patient_id} 的映射记录数: {len(mappings)}")
                
                scans = Scan.query.filter_by(patient_id=patient_id).all()
                logger.info(f"患者 {patient_id} 的扫描记录数: {len(scans)}")
                
                if len(mappings) != len(scan_ids) or len(scans) != len(scan_ids):
                    logger.warning(f"患者 {patient_id} 的记录数不匹配: 映射={len(mappings)}, 扫描={len(scans)}, 预期={len(scan_ids)}")
            
    except Exception as e:
        logger.error(f"更新患者与扫描记录的关系时出错: {str(e)}")
        db.session.rollback()
        raise

def main():
    """主函数"""
    logger.info("开始更新患者与扫描记录的关系...")
    update_patient_scan_relations()
    logger.info("更新完成！")

if __name__ == "__main__":
    main() 