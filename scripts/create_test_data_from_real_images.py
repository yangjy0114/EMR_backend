import sys
import os
import random
import shutil
from datetime import datetime, timedelta
from PIL import Image

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Patient, User, Scan, MedicalRecord, Diagnosis, Prescription
from werkzeug.security import generate_password_hash

# 测试图片目录
TEST_IMAGES_DIR = 'images/test_images'

def create_test_data():
    """创建测试患者和扫描记录，使用真实图片"""
    with app.app_context():
        try:
            # 确保目录存在
            os.makedirs(TEST_IMAGES_DIR, exist_ok=True)
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'scans'), exist_ok=True)
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'originals'), exist_ok=True)
            os.makedirs('images/segmentation', exist_ok=True)
            
            # 检查测试图片是否存在
            test_images = os.listdir(TEST_IMAGES_DIR)
            if not test_images:
                print(f"错误: 测试图片目录 {TEST_IMAGES_DIR} 为空。请先上传测试图片。")
                return
                
            print(f"发现 {len(test_images)} 个测试图片文件")
            
            # 清空现有数据 - 按照正确的顺序删除以避免外键约束错误
            print("清空现有数据...")
            # 首先删除依赖于其他表的记录
            db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0"))
            
            # 删除诊断和处方
            Diagnosis.query.delete()
            Prescription.query.delete()
            
            # 删除医疗记录
            MedicalRecord.query.delete()
            
            # 删除扫描记录
            Scan.query.delete()
            
            # 删除患者
            Patient.query.delete()
            
            db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1"))
            db.session.commit()
            print("数据清空完成")
            
            # 确保有一个医生用户
            doctor = User.query.filter_by(username='doctor').first()
            if not doctor:
                doctor = User(
                    username='doctor',
                    password=generate_password_hash('password'),
                    real_name='测试医生',
                    department_id=1
                )
                db.session.add(doctor)
                db.session.commit()
            
            # 创建10个患者
            patients = []
            for i in range(1, 11):
                gender = '男' if i % 2 == 0 else '女'
                # 使用age而不是birthdate
                age = 20 + i
                
                patient = Patient(
                    name=f'测试患者{i}',
                    gender=gender,
                    age=age,
                    serial_no=f'SN{i:04d}',
                    card_no=f'CN{i:04d}',
                    status='active'
                )
                db.session.add(patient)
                db.session.flush()  # 获取ID
                patients.append(patient)
            
            # 获取所有图片文件
            all_images = sorted(test_images)
            fundus_images = sorted([f for f in all_images if 'fundus' in f.lower()])
            oct_images = sorted([f for f in all_images if 'oct' in f.lower()])
            
            print(f"发现 {len(fundus_images)} 个眼底图像和 {len(oct_images)} 个OCT图像")
            
            # 确保眼底图像和OCT图像数量相同
            if len(fundus_images) != len(oct_images):
                print(f"警告: 眼底图像数量 ({len(fundus_images)}) 与OCT图像数量 ({len(oct_images)}) 不匹配")
                # 取最小值
                image_count = min(len(fundus_images), len(oct_images))
                fundus_images = fundus_images[:image_count]
                oct_images = oct_images[:image_count]
            else:
                image_count = len(fundus_images)
                
            print(f"将使用 {image_count} 对图像创建扫描记录")
            
            # 为第一个患者创建4份扫描记录
            for i in range(min(4, image_count)):
                create_scan_from_images(
                    patients[0], 
                    doctor, 
                    i+1,
                    os.path.join(TEST_IMAGES_DIR, fundus_images[i]),
                    os.path.join(TEST_IMAGES_DIR, oct_images[i])
                )
            
            # 为第二个患者创建3份扫描记录
            for i in range(4, min(7, image_count)):
                create_scan_from_images(
                    patients[1], 
                    doctor, 
                    i+1,
                    os.path.join(TEST_IMAGES_DIR, fundus_images[i]),
                    os.path.join(TEST_IMAGES_DIR, oct_images[i])
                )
            
            # 为剩下8个患者各创建1份扫描记录
            for i in range(7, min(15, image_count)):
                patient_idx = i - 5  # 从第3个患者开始
                if patient_idx < len(patients):
                    create_scan_from_images(
                        patients[patient_idx], 
                        doctor, 
                        i+1,
                        os.path.join(TEST_IMAGES_DIR, fundus_images[i]),
                        os.path.join(TEST_IMAGES_DIR, oct_images[i])
                    )
            
            db.session.commit()
            print(f"成功创建10个患者和扫描记录")
            
        except Exception as e:
            db.session.rollback()
            print(f"创建测试数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()

def create_scan_from_images(patient, doctor, scan_count, fundus_path, oct_path):
    """使用真实图片为患者创建扫描记录"""
    timestamp = datetime.now() - timedelta(days=scan_count)
    timestamp_str = timestamp.strftime('%Y%m%d%H%M%S')
    
    # 创建显示用的图像文件名
    oct_display_filename = f"{patient.id}_OCT_{timestamp_str}.png"
    fundus_display_filename = f"{patient.id}_Fundus_{timestamp_str}.png"
    
    # 创建原始图像文件名
    oct_original_filename = f"{patient.id}_OCT_original_{timestamp_str}.tif"
    fundus_original_filename = f"{patient.id}_Fundus_original_{timestamp_str}.tif"
    
    # 复制并转换图像
    # 1. 复制原始TIF图像
    shutil.copy(
        fundus_path, 
        os.path.join(app.config['UPLOAD_FOLDER'], 'originals', fundus_original_filename)
    )
    shutil.copy(
        oct_path, 
        os.path.join(app.config['UPLOAD_FOLDER'], 'originals', oct_original_filename)
    )
    
    # 2. 创建显示用的PNG图像
    convert_to_png(
        fundus_path, 
        os.path.join(app.config['UPLOAD_FOLDER'], 'scans', fundus_display_filename)
    )
    convert_to_png(
        oct_path, 
        os.path.join(app.config['UPLOAD_FOLDER'], 'scans', oct_display_filename)
    )
    
    # 创建扫描记录
    scan = Scan(
        patient_id=patient.id,
        doctor_id=doctor.id,
        scan_type='Both',
        scan_time=timestamp,
        oct_image_path=f"/api/images/{oct_display_filename}",
        fundus_image_path=f"/api/images/{fundus_display_filename}",
        oct_original_path=f"/api/originals/{oct_original_filename}",
        fundus_original_path=f"/api/originals/{fundus_original_filename}"
    )
    db.session.add(scan)
    print(f"为患者 {patient.name} 创建了扫描记录，使用图像 {os.path.basename(fundus_path)} 和 {os.path.basename(oct_path)}")

def convert_to_png(source_path, target_path):
    """将图像转换为PNG格式"""
    try:
        img = Image.open(source_path)
        # 如果是多页TIF，只取第一页
        if hasattr(img, 'n_frames') and img.n_frames > 1:
            img.seek(0)
        
        # 转换为RGB模式（如果是RGBA或其他模式）
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # 保存为PNG
        img.save(target_path, 'PNG')
    except Exception as e:
        print(f"转换图像 {source_path} 时出错: {str(e)}")
        # 创建一个替代图像
        img = Image.new('RGB', (512, 512), color=(73, 109, 137))
        img.save(target_path, 'PNG')

if __name__ == "__main__":
    create_test_data() 