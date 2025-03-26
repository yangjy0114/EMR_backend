import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Scan, Patient, User

def list_all_scans():
    """列出所有扫描记录"""
    with app.app_context():
        try:
            # 获取所有扫描记录，并按ID排序
            scans = Scan.query.order_by(Scan.id).all()
            
            if not scans:
                print("数据库中没有扫描记录")
                return
            
            print(f"找到 {len(scans)} 条扫描记录：")
            print("-" * 100)
            print(f"{'ID':<5} | {'患者ID':<8} | {'患者姓名':<10} | {'医生':<10} | {'扫描类型':<8} | {'扫描时间':<20} | {'OCT图像':<30} | {'眼底图像':<30}")
            print("-" * 100)
            
            for scan in scans:
                # 获取患者信息
                patient = Patient.query.get(scan.patient_id)
                patient_name = patient.name if patient else "未知"
                
                # 获取医生信息
                doctor = User.query.get(scan.doctor_id)
                doctor_name = doctor.real_name if doctor else "未知"
                
                # 格式化扫描时间
                scan_time = scan.scan_time.strftime('%Y-%m-%d %H:%M:%S') if scan.scan_time else "未知"
                
                # 获取图像路径的文件名部分
                oct_image = os.path.basename(scan.oct_image_path) if scan.oct_image_path else "无"
                fundus_image = os.path.basename(scan.fundus_image_path) if scan.fundus_image_path else "无"
                
                # 打印扫描记录信息
                print(f"{scan.id:<5} | {scan.patient_id:<8} | {patient_name:<10} | {doctor_name:<10} | {scan.scan_type:<8} | {scan_time:<20} | {oct_image:<30} | {fundus_image:<30}")
            
            print("-" * 100)
            
            # 打印患者ID与分类结果的对应关系
            print("\n患者ID与分类结果对应关系：")
            print("-" * 40)
            print(f"{'患者ID':<8} | {'患者姓名':<10} | {'分类结果':<20}")
            print("-" * 40)
            
            patients = Patient.query.order_by(Patient.id).all()
            for patient in patients:
                classification = ""
                remainder = patient.id % 3
                if remainder == 1:
                    classification = "AMD（年龄相关性黄斑变性）"
                elif remainder == 2:
                    classification = "DME（糖尿病黄斑水肿）"
                else:  # remainder == 0
                    classification = "正常（无明显病变）"
                
                print(f"{patient.id:<8} | {patient.name:<10} | {classification:<20}")
            
        except Exception as e:
            print(f"列出扫描记录时出错: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    list_all_scans() 