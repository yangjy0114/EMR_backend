import os
import sys
import time
import shutil
import threading

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
            shutil.rmtree(folder)

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
                # 可选: 自动删除
                # shutil.rmtree(folder)
        
        # 每秒检查一次
        time.sleep(1)

def main():
    """主函数"""
    # 首先清理文件夹
    cleanup_folders()
    
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