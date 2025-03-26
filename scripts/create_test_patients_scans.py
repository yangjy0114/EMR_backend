import sys
import os
import random
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Patient, User, Scan
from werkzeug.security import generate_password_hash

def create_test_data():
    """创建测试患者和扫描记录"""
    with app.app_context():
        try:
            # 清空现有数据
            Scan.query.delete()
            Patient.query.delete()
            
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
                birth_date = datetime.now() - timedelta(days=365 * (20 + i))
                
                patient = Patient(
                    name=f'测试患者{i}',
                    gender=gender,
                    birth_date=birth_date,
                    phone=f'1380000{i:04d}',
                    address=f'测试地址{i}',
                    medical_history='无',
                    allergies='无'
                )
                db.session.add(patient)
                db.session.flush()  # 获取ID
                patients.append(patient)
            
            # 为患者创建扫描记录
            scan_count = 0
            
            # 第一个患者4份扫描记录
            for _ in range(4):
                scan_count += 1
                create_scan(patients[0], doctor, scan_count)
            
            # 第二个患者3份扫描记录
            for _ in range(3):
                scan_count += 1
                create_scan(patients[1], doctor, scan_count)
            
            # 剩下8个患者各1份扫描记录
            for i in range(2, 10):
                scan_count += 1
                create_scan(patients[i], doctor, scan_count)
            
            db.session.commit()
            print(f"成功创建10个患者和15份扫描记录")
            
        except Exception as e:
            db.session.rollback()
            print(f"创建测试数据时出错: {str(e)}")

def create_scan(patient, doctor, scan_count):
    """为患者创建扫描记录"""
    timestamp = datetime.now() - timedelta(days=scan_count)
    timestamp_str = timestamp.strftime('%Y%m%d%H%M%S')
    
    # 创建显示用的图像路径
    oct_filename = f"{patient.id}_OCT_{timestamp_str}.png"
    fundus_filename = f"{patient.id}_Fundus_{timestamp_str}.png"
    
    # 创建原始图像路径
    oct_original = f"{patient.id}_OCT_original_{timestamp_str}.tif"
    fundus_original = f"{patient.id}_Fundus_original_{timestamp_str}.tif"
    
    scan = Scan(
        patient_id=patient.id,
        doctor_id=doctor.id,
        scan_type='Both',
        scan_time=timestamp,
        oct_image_path=f"/api/images/{oct_filename}",
        fundus_image_path=f"/api/images/{fundus_filename}",
        oct_original_path=f"/api/originals/{oct_original}",
        fundus_original_path=f"/api/originals/{fundus_original}"
    )
    db.session.add(scan)
    
    # 创建模拟图像文件
    create_mock_image(os.path.join(app.config['UPLOAD_FOLDER'], 'scans', oct_filename))
    create_mock_image(os.path.join(app.config['UPLOAD_FOLDER'], 'scans', fundus_filename))
    create_mock_image(os.path.join(app.config['UPLOAD_FOLDER'], 'originals', oct_original))
    create_mock_image(os.path.join(app.config['UPLOAD_FOLDER'], 'originals', fundus_original))

def create_mock_image(file_path):
    """创建模拟图像文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 使用PIL创建一个简单的图像
    from PIL import Image, ImageDraw
    
    # 创建一个512x512的图像
    img = Image.new('RGB', (512, 512), color=(73, 109, 137))
    
    # 添加一些随机形状
    d = ImageDraw.Draw(img)
    for i in range(10):
        x1 = random.randint(0, 512)
        y1 = random.randint(0, 512)
        x2 = random.randint(0, 512)
        y2 = random.randint(0, 512)
        d.ellipse([x1, y1, x2, y2], fill=(255, 255, 255, 128))
    
    # 保存图像
    img.save(file_path)

if __name__ == "__main__":
    create_test_data() 