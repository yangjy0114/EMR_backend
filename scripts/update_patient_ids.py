import os
import sys
import logging

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入必要的模块
from app import app, db
from models import Scan

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_patient_ids():
    """更新scans表中的patient_id字段"""
    try:
        with app.app_context():
            # 定义扫描记录与患者的映射关系
            scan_patient_mapping = {
                # 患者1的扫描记录
                1: 1,
                2: 1,
                3: 1,
                4: 1,
                
                # 患者2的扫描记录
                5: 2,
                6: 2,
                7: 2,
                
                # 患者3-10的扫描记录
                8: 3,
                9: 4,
                10: 5,
                11: 6,
                12: 7,
                13: 8,
                14: 9,
                15: 10
            }
            
            # 更新patient_id
            for scan_id, patient_id in scan_patient_mapping.items():
                scan = Scan.query.get(scan_id)
                if scan:
                    old_patient_id = scan.patient_id
                    scan.patient_id = patient_id
                    logger.info(f"更新扫描记录: scan_id={scan_id}, patient_id={old_patient_id} -> {patient_id}")
                else:
                    logger.warning(f"扫描记录不存在: scan_id={scan_id}")
            
            # 提交更改
            db.session.commit()
            logger.info("更新完成！")
            
            # 验证更新结果
            for patient_id in range(1, 11):
                scans = Scan.query.filter_by(patient_id=patient_id).all()
                logger.info(f"患者 {patient_id} 的扫描记录数: {len(scans)}")
                for scan in scans:
                    logger.info(f"  - scan_id={scan.id}, patient_id={scan.patient_id}")
            
    except Exception as e:
        logger.error(f"更新patient_id时出错: {str(e)}")
        db.session.rollback()
        raise

def main():
    """主函数"""
    logger.info("开始更新scans表中的patient_id字段...")
    update_patient_ids()
    logger.info("更新完成！")

if __name__ == "__main__":
    main() 