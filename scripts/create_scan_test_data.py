import sys
import os
import shutil

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Scan, Patient, User
from datetime import datetime, timedelta

def create_scan_test_data():
    with app.app_context():
        try:
            # 获取测试患者和医生
            patient = Patient.query.filter_by(serial_no='202005090006').first()  # 张明
            doctor = User.query.filter_by(username='doctor1').first()
            
            if not patient or not doctor:
                print("找不到测试患者或医生，请先创建患者和用户测试数据")
                return
                
            # 确保上传目录存在
            upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'scans')
            os.makedirs(upload_folder, exist_ok=True)
            
            # 准备测试图像
            mock_images_dir = os.path.join('mock', 'images')
            os.makedirs(os.path.join(mock_images_dir, 'oct'), exist_ok=True)
            os.makedirs(os.path.join(mock_images_dir, 'fundus'), exist_ok=True)
            
            # 创建示例图像（如果不存在）
            oct_sample = os.path.join(mock_images_dir, 'oct', 'p001_oct.png')
            fundus_sample = os.path.join(mock_images_dir, 'fundus', 'p001_fundus.png')
            
            # 如果示例图像不存在，创建空白图像
            if not os.path.exists(oct_sample):
                with open(oct_sample, 'w') as f:
                    f.write("This is a placeholder for OCT image")
                    
            if not os.path.exists(fundus_sample):
                with open(fundus_sample, 'w') as f:
                    f.write("This is a placeholder for fundus image")
            
            # 创建测试扫描记录
            timestamp = datetime.utcnow() - timedelta(days=3)
            timestamp_str = timestamp.strftime('%Y%m%d%H%M%S')
            
            # 复制示例图像到上传目录
            oct_filename = f"{patient.id}_OCT_{timestamp_str}.png"
            fundus_filename = f"{patient.id}_Fundus_{timestamp_str}.png"
            
            oct_dest = os.path.join(upload_folder, oct_filename)
            fundus_dest = os.path.join(upload_folder, fundus_filename)
            
            shutil.copy(oct_sample, oct_dest)
            shutil.copy(fundus_sample, fundus_dest)
            
            # 创建扫描记录
            scan = Scan(
                patient_id=patient.id,
                doctor_id=doctor.id,
                scan_type='Both',
                scan_time=timestamp,
                oct_image_path=f"/api/images/{oct_filename}",
                fundus_image_path=f"/api/images/{fundus_filename}"
            )
            db.session.add(scan)
            db.session.commit()
            
            print("扫描测试数据创建成功！")
            print(f"OCT图像路径: {scan.oct_image_path}")
            print(f"眼底图像路径: {scan.fundus_image_path}")
            
        except Exception as e:
            print(f"创建扫描测试数据时出错: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    create_scan_test_data() 