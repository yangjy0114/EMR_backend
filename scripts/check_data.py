# scripts/check_data.py
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, MedicalRecord, Scan, Patient

def check_data():
    with app.app_context():
        # 检查患者记录
        patients = Patient.query.all()
        print(f"患者记录数量: {len(patients)}")
        for patient in patients:
            print(f"患者ID: {patient.id}, 姓名: {patient.name}, 流水号: {patient.serial_no}")
        
        # 检查病历记录
        records = MedicalRecord.query.all()
        print(f"\n病历记录数量: {len(records)}")
        for record in records:
            print(f"病历ID: {record.id}, 患者ID: {record.patient_id}")
        
        # 检查扫描记录
        scans = Scan.query.all()
        print(f"\n扫描记录数量: {len(scans)}")
        for scan in scans:
            print(f"扫描ID: {scan.id}, 患者ID: {scan.patient_id}, OCT图像: {scan.oct_image_path}, 眼底图像: {scan.fundus_image_path}")

if __name__ == "__main__":
    check_data()