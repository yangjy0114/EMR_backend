from app import app, db
from models import Patient, Doctor, Scan, Image, SegmentedImage, ClassificationResult, Report
from tabulate import tabulate
import sys

def print_table(data, title):
    """格式化打印表格数据"""
    if not data:
        print(f"\n{title} 表为空")
        return
        
    # 获取对象的属性
    headers = [column.name for column in data[0].__table__.columns]
    rows = [[getattr(item, column) for column in headers] for item in data]
    
    print(f"\n{title}:")
    print(tabulate(rows, headers=headers, tablefmt='grid'))

def query_all_tables():
    """查询所有表的数据"""
    with app.app_context():
        try:
            # 查询所有表
            patients = Patient.query.all()
            doctors = Doctor.query.all()
            scans = Scan.query.all()
            images = Image.query.all()
            segmented_images = SegmentedImage.query.all()
            classification_results = ClassificationResult.query.all()
            reports = Report.query.all()
            
            # 打印各表数据
            print_table(patients, "患者表")
            print_table(doctors, "医生表")
            print_table(scans, "扫描记录表")
            print_table(images, "图像表")
            print_table(segmented_images, "分割图像表")
            print_table(classification_results, "分类结果表")
            print_table(reports, "报告表")
            
        except Exception as e:
            print(f"查询数据库时出错: {str(e)}")

def query_specific_table(table_name):
    """查询指定表的数据"""
    table_map = {
        'patient': Patient,
        'doctor': Doctor,
        'scan': Scan,
        'image': Image,
        'segmented': SegmentedImage,
        'classification': ClassificationResult,
        'report': Report
    }
    
    if table_name not in table_map:
        print(f"错误：未知的表名 '{table_name}'")
        print(f"可用的表名: {', '.join(table_map.keys())}")
        return
        
    with app.app_context():
        try:
            data = table_map[table_name].query.all()
            print_table(data, f"{table_name}表")
        except Exception as e:
            print(f"查询表 {table_name} 时出错: {str(e)}")

if __name__ == "__main__":
    # 添加 tabulate 到 requirements.txt
    if len(sys.argv) > 1:
        query_specific_table(sys.argv[1])
    else:
        query_all_tables() 