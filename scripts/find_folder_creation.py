import os
import re

def find_folder_creation():
    """查找所有可能创建文件夹的代码"""
    # 要搜索的目录
    search_dirs = ['.', 'routes', 'services', 'scripts']
    
    # 要查找的文件夹路径模式
    folder_patterns = [
        r'images/original',
        r'images/originals',
        r'images/scans',
        r'images/segmented',
        r'uploads/original',
        r'uploads/originals',
        r'uploads/scans',
        r'uploads/segmented'
    ]
    
    # 编译正则表达式
    patterns = [re.compile(pattern.replace('/', r'[/\\]')) for pattern in folder_patterns]
    
    # 查找所有Python文件
    for search_dir in search_dirs:
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # 查找os.makedirs或类似的调用
                            for i, pattern in enumerate(patterns):
                                if pattern.search(content):
                                    print(f"在文件 {file_path} 中找到可能创建 {folder_patterns[i]} 的代码")
                                    
                            # 查找os.path.join与这些路径相关的代码
                            for folder in folder_patterns:
                                folder_parts = folder.split('/')
                                if len(folder_parts) > 1 and f"os.path.join('{folder_parts[0]}'," in content:
                                    print(f"在文件 {file_path} 中找到可能使用 {folder} 的os.path.join调用")
                    except Exception as e:
                        print(f"读取文件 {file_path} 时出错: {str(e)}")

if __name__ == "__main__":
    find_folder_creation() 