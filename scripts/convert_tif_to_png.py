import os
import sys
from PIL import Image

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def convert_tif_to_png():
    """将TIF图像转换为PNG格式"""
    # 确保目标目录存在
    os.makedirs('images/pngs/fundus', exist_ok=True)
    os.makedirs('images/pngs/oct', exist_ok=True)
    
    # 转换眼底图像
    fundus_dir = 'images/tifs/fundus'
    if os.path.exists(fundus_dir):
        for filename in os.listdir(fundus_dir):
            if filename.endswith('.tif'):
                tif_path = os.path.join(fundus_dir, filename)
                png_filename = filename.replace('.tif', '.png')
                png_path = os.path.join('images/pngs/fundus', png_filename)
                
                try:
                    img = Image.open(tif_path)
                    # 如果是多页TIF，只取第一页
                    if hasattr(img, 'n_frames') and img.n_frames > 1:
                        img.seek(0)
                    
                    # 转换为RGB模式（如果是RGBA或其他模式）
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                        
                    # 保存为PNG
                    img.save(png_path, 'PNG')
                    print(f"转换成功: {tif_path} -> {png_path}")
                except Exception as e:
                    print(f"转换失败: {tif_path}, 错误: {str(e)}")
    
    # 转换OCT图像
    oct_dir = 'images/tifs/oct'
    if os.path.exists(oct_dir):
        for filename in os.listdir(oct_dir):
            if filename.endswith('.tif'):
                tif_path = os.path.join(oct_dir, filename)
                png_filename = filename.replace('.tif', '.png')
                png_path = os.path.join('images/pngs/oct', png_filename)
                
                try:
                    img = Image.open(tif_path)
                    # 如果是多页TIF，只取第一页
                    if hasattr(img, 'n_frames') and img.n_frames > 1:
                        img.seek(0)
                    
                    # 转换为RGB模式（如果是RGBA或其他模式）
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                        
                    # 保存为PNG
                    img.save(png_path, 'PNG')
                    print(f"转换成功: {tif_path} -> {png_path}")
                except Exception as e:
                    print(f"转换失败: {tif_path}, 错误: {str(e)}")

if __name__ == "__main__":
    convert_tif_to_png() 