import sys
import os
import re
from datetime import datetime, timedelta
import random

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Patient, User, Scan, AIAnalysisResult
from sqlalchemy import text

def rebuild_scan_records():
    """重建扫描记录，将图像与患者关联"""
    with app.app_context():
        try:
            print("开始重建扫描记录...")
            
            # 清空现有的扫描记录和AI分析结果
            db.session.execute(text("DELETE FROM ai_analysis_results"))
            db.session.execute(text("DELETE FROM scans"))
            db.session.commit()
            
            # 获取所有患者
            patients = Patient.query.order_by(Patient.id).all()
            if not patients:
                print("错误：数据库中没有患者记录")
                return
                
            # 获取一个医生用户
            doctor = User.query.first()
            if not doctor:
                print("错误：数据库中没有医生用户")
                return
            
            # 确保分割结果目录存在
            os.makedirs('images/segmentation', exist_ok=True)
            
            # 获取所有图像文件
            fundus_files = []
            oct_files = []
            
            # 获取眼底图像
            fundus_dir = 'images/tifs/fundus'
            if os.path.exists(fundus_dir):
                for filename in os.listdir(fundus_dir):
                    if filename.endswith('.tif'):
                        fundus_files.append(filename)
            
            # 获取OCT图像
            oct_dir = 'images/tifs/oct'
            if os.path.exists(oct_dir):
                for filename in os.listdir(oct_dir):
                    if filename.endswith('.tif'):
                        oct_files.append(filename)
            
            # 按照患者ID排序图像
            fundus_files.sort()
            oct_files.sort()
            
            # 创建患者ID到图像的映射
            patient_images = {}
            
            # 解析文件名中的患者ID
            for filename in fundus_files:
                match = re.match(r'p(\d+)_fundus\.tif', filename)
                if match:
                    patient_num = int(match.group(1))
                    if patient_num not in patient_images:
                        patient_images[patient_num] = {'fundus': [], 'oct': []}
                    patient_images[patient_num]['fundus'].append(filename)
            
            for filename in oct_files:
                match = re.match(r'p(\d+)_oct\.tif', filename)
                if match:
                    patient_num = int(match.group(1))
                    if patient_num not in patient_images:
                        patient_images[patient_num] = {'fundus': [], 'oct': []}
                    patient_images[patient_num]['oct'].append(filename)
            
            # 创建扫描记录
            scan_id = 1
            
            # 为每个患者创建扫描记录
            for patient_num, images in sorted(patient_images.items()):
                # 找到对应的患者记录
                patient = None
                for p in patients:
                    if p.id == patient_num:
                        patient = p
                        break
                
                if not patient and patients:
                    # 如果找不到对应ID的患者，使用第一个患者
                    patient = patients[0]
                    print(f"警告：找不到ID为{patient_num}的患者，使用ID为{patient.id}的患者")
                
                if not patient:
                    print(f"错误：无法为患者{patient_num}创建扫描记录")
                    continue
                
                # 创建扫描记录
                fundus_list = images.get('fundus', [])
                oct_list = images.get('oct', [])
                
                # 确定要创建的扫描记录数量
                scan_count = max(len(fundus_list), len(oct_list))
                
                for i in range(scan_count):
                    # 生成扫描时间（过去30天内随机时间）
                    days_ago = random.randint(0, 30)
                    scan_time = datetime.now() - timedelta(days=days_ago)
                    
                    # 确定此次扫描使用的图像
                    fundus_file = fundus_list[i % len(fundus_list)] if fundus_list else None
                    oct_file = oct_list[i % len(oct_list)] if oct_list else None
                    
                    # 确定扫描类型
                    if fundus_file and oct_file:
                        scan_type = 'Both'
                    elif fundus_file:
                        scan_type = 'Fundus'
                    elif oct_file:
                        scan_type = 'OCT'
                    else:
                        continue  # 跳过没有图像的扫描
                    
                    # 创建扫描记录
                    scan = Scan(
                        id=scan_id,
                        patient_id=patient.id,
                        doctor_id=doctor.id,
                        scan_type=scan_type,
                        scan_time=scan_time
                    )
                    
                    # 设置图像路径
                    if fundus_file:
                        # TIF路径
                        fundus_tif_path = f"images/tifs/fundus/{fundus_file}"
                        # PNG路径
                        fundus_png_file = fundus_file.replace('.tif', '.png')
                        fundus_png_path = f"images/pngs/fundus/{fundus_png_file}"
                        
                        # 设置API路径
                        scan.fundus_original_path = f"/api/tifs/fundus/{fundus_file}"
                        scan.fundus_image_path = f"/api/pngs/fundus/{fundus_png_file}"
                    
                    if oct_file:
                        # TIF路径
                        oct_tif_path = f"images/tifs/oct/{oct_file}"
                        # PNG路径
                        oct_png_file = oct_file.replace('.tif', '.png')
                        oct_png_path = f"images/pngs/oct/{oct_png_file}"
                        
                        # 设置API路径
                        scan.oct_original_path = f"/api/tifs/oct/{oct_file}"
                        scan.oct_image_path = f"/api/pngs/oct/{oct_png_file}"
                    
                    db.session.add(scan)
                    print(f"创建扫描记录 ID={scan_id}, 患者ID={patient.id}, 类型={scan_type}")
                    scan_id += 1
            
            db.session.commit()
            print(f"成功创建了 {scan_id-1} 条扫描记录")
            
        except Exception as e:
            print(f"重建扫描记录时出错: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    rebuild_scan_records() 