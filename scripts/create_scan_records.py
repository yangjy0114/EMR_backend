import sys
import os
import random
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Patient, User, Scan
from sqlalchemy import text

def create_scan_records():
    """创建扫描记录，按照指定的分配规则"""
    with app.app_context():
        try:
            print("开始创建扫描记录...")
            
            # 清空现有的扫描记录
            db.session.execute(text("DELETE FROM ai_analysis_results"))
            db.session.execute(text("DELETE FROM scans"))
            db.session.commit()
            
            # 获取所有患者
            patients = Patient.query.order_by(Patient.id).all()
            if not patients or len(patients) < 10:
                print("错误：数据库中没有足够的患者记录（需要至少10个）")
                return
                
            # 获取一个医生用户
            doctor = User.query.first()
            if not doctor:
                print("错误：数据库中没有医生用户")
                return
                
            # 确保目录存在
            os.makedirs('images/originals', exist_ok=True)
            os.makedirs('images/scans', exist_ok=True)
            
            # 创建测试图像（如果不存在）
            create_test_images()
            
            # 分配扫描记录：前4次给第一个患者，5-7次给第二个患者，8-15次给剩下8个患者
            scan_distribution = {
                patients[0].id: 4,  # 第一个患者4次扫描
                patients[1].id: 3,  # 第二个患者3次扫描
            }
            
            # 剩下8个患者各1次扫描
            for i in range(2, 10):
                scan_distribution[patients[i].id] = 1
                
            # 创建扫描记录
            scan_id = 1
            for patient_id, scan_count in scan_distribution.items():
                for i in range(scan_count):
                    # 生成扫描时间（过去30天内随机时间）
                    days_ago = random.randint(0, 30)
                    scan_time = datetime.now() - timedelta(days=days_ago)
                    
                    # 生成文件名
                    timestamp = scan_time.strftime('%Y%m%d%H%M%S')
                    tif_filename = f"scan_{scan_id}_patient_{patient_id}_{timestamp}.tif"
                    png_filename = f"scan_{scan_id}_patient_{patient_id}_{timestamp}.png"
                    
                    # 创建TIF和PNG测试图像
                    tif_path = os.path.join('images/originals', tif_filename)
                    png_path = os.path.join('images/scans', png_filename)
                    
                    # 创建或复制测试图像
                    create_test_image(tif_path, png_path)
                    
                    # 创建扫描记录
                    scan = Scan(
                        id=scan_id,  # 明确设置ID
                        patient_id=patient_id,
                        doctor_id=doctor.id,
                        scan_type='Fundus',  # 或者根据需要设置
                        scan_time=scan_time,
                        fundus_image_path=f"/api/images/{png_filename}",
                        fundus_original_path=f"/api/originals/{tif_filename}"
                    )
                    db.session.add(scan)
                    
                    print(f"创建扫描记录 ID={scan_id}, 患者ID={patient_id}")
                    scan_id += 1
            
            db.session.commit()
            print(f"成功创建了 {scan_id-1} 条扫描记录")
            
        except Exception as e:
            print(f"创建扫描记录时出错: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

def create_test_images():
    """创建测试图像模板"""
    from PIL import Image, ImageDraw
    
    # 创建一个基本的眼底图像模板
    template_path = 'images/template_fundus.png'
    if not os.path.exists(template_path):
        img = Image.new('RGB', (512, 512), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 绘制一个圆形，模拟眼底
        center_x, center_y = 256, 256
        radius = 200
        draw.ellipse((center_x-radius, center_y-radius, center_x+radius, center_y+radius), 
                     fill=(150, 100, 50))
        
        # 绘制一些血管
        for i in range(20):
            start_x = center_x
            start_y = center_y
            end_x = center_x + random.randint(-radius, radius)
            end_y = center_y + random.randint(-radius, radius)
            
            # 确保线条在圆内
            dist = ((end_x - center_x)**2 + (end_y - center_y)**2)**0.5
            if dist > radius:
                scale = radius / dist * 0.9
                end_x = center_x + int((end_x - center_x) * scale)
                end_y = center_y + int((end_y - center_y) * scale)
                
            draw.line((start_x, start_y, end_x, end_y), fill=(200, 50, 50), width=2)
        
        # 保存模板
        img.save(template_path)
        print(f"创建了眼底图像模板: {template_path}")

def create_test_image(tif_path, png_path):
    """创建或复制测试图像"""
    from PIL import Image, ImageDraw
    
    # 使用模板创建新图像
    template_path = 'images/template_fundus.png'
    if os.path.exists(template_path):
        # 复制并修改模板
        img = Image.open(template_path)
        draw = ImageDraw.Draw(img)
        
        # 添加一些随机变化
        center_x, center_y = 256, 256
        for i in range(5):
            x = center_x + random.randint(-100, 100)
            y = center_y + random.randint(-100, 100)
            size = random.randint(10, 30)
            draw.ellipse((x-size, y-size, x+size, y+size), 
                         fill=(random.randint(100, 255), random.randint(0, 100), random.randint(0, 100)))
        
        # 保存为TIF和PNG
        img.save(tif_path)
        img.save(png_path)
    else:
        # 如果没有模板，创建简单的图像
        img = Image.new('RGB', (512, 512), color=(random.randint(50, 150), random.randint(50, 150), random.randint(50, 150)))
        draw = ImageDraw.Draw(img)
        
        # 添加一些随机形状
        for i in range(10):
            x = random.randint(0, 512)
            y = random.randint(0, 512)
            size = random.randint(20, 100)
            draw.ellipse((x-size, y-size, x+size, y+size), 
                         fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        
        # 保存为TIF和PNG
        img.save(tif_path)
        img.save(png_path)
    
    print(f"创建了测试图像: {tif_path} 和 {png_path}")

if __name__ == "__main__":
    create_scan_records() 