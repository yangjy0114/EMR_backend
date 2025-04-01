import os
import sys
import shutil

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def cleanup_folders():
    """清理不需要的文件夹"""
    # 需要删除的文件夹
    folders_to_remove = [
        'images/original',
        'images/originals',
        'images/scans',
        'images/segmented',
        'images/test_images'
    ]
    
    # 需要保留的文件夹
    folders_to_keep = [
        'images/tifs/fundus',
        'images/tifs/oct',
        'images/pngs/fundus',
        'images/pngs/oct',
        'images/segmentation/fundus',
        'images/segmentation/oct'
    ]
    
    # 删除不需要的文件夹
    for folder in folders_to_remove:
        if os.path.exists(folder):
            print(f"删除文件夹: {folder}")
            shutil.rmtree(folder)
    
    # 确保需要的文件夹存在
    for folder in folders_to_keep:
        os.makedirs(folder, exist_ok=True)
        print(f"确保文件夹存在: {folder}")
    
    print("文件夹清理完成！")

if __name__ == "__main__":
    cleanup_folders() 