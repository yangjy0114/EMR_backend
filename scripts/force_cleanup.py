import os
import sys
import shutil
import time
import threading

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def force_cleanup():
    """强制清理不需要的文件夹"""
    # 需要删除的文件夹
    folders_to_remove = [
        'images/original',
        'images/originals',
        'images/scans',
        'images/segmented',
        'images/test_images',
        'uploads/original',
        'uploads/originals',
        'uploads/scans',
        'uploads/segmented'
    ]
    
    # 删除不需要的文件夹
    for folder in folders_to_remove:
        if os.path.exists(folder):
            print(f"删除文件夹: {folder}")
            try:
                shutil.rmtree(folder)
            except Exception as e:
                print(f"删除文件夹 {folder} 时出错: {str(e)}")
                # 尝试删除文件夹中的所有文件
                try:
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                os.remove(file_path)
                                print(f"  删除文件: {file_path}")
                            except Exception as e2:
                                print(f"  删除文件 {file_path} 时出错: {str(e2)}")
                except Exception as e3:
                    print(f"遍历文件夹 {folder} 时出错: {str(e3)}")

def monitor_folders():
    """监控文件夹是否被重新创建"""
    # 需要监控的文件夹
    folders_to_monitor = [
        'images/original',
        'images/originals',
        'images/scans',
        'images/segmented',
        'images/test_images',
        'uploads/original',
        'uploads/originals',
        'uploads/scans',
        'uploads/segmented'
    ]
    
    while True:
        for folder in folders_to_monitor:
            if os.path.exists(folder):
                print(f"警告: 文件夹 {folder} 被重新创建了!")
                # 自动删除
                try:
                    shutil.rmtree(folder)
                    print(f"  已自动删除文件夹: {folder}")
                except Exception as e:
                    print(f"  自动删除文件夹 {folder} 时出错: {str(e)}")
        
        # 每秒检查一次
        time.sleep(1)

def main():
    """主函数"""
    # 首先强制清理文件夹
    force_cleanup()
    
    # 启动监控线程
    monitor_thread = threading.Thread(target=monitor_folders)
    monitor_thread.daemon = True  # 设置为守护线程，这样主程序退出时线程也会退出
    monitor_thread.start()
    
    print("监控已启动，按Ctrl+C退出...")
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("监控已停止")

if __name__ == "__main__":
    main() 