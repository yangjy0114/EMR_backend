import os
import re
import sys

def search_file_for_patterns(file_path, patterns):
    """搜索文件中的模式"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            results = []
            for pattern in patterns:
                if pattern.search(content):
                    results.append(pattern)
            
            return results
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {str(e)}")
        return []

def search_directory(directory, patterns, exclude_dirs=None):
    """递归搜索目录中的所有Python文件"""
    if exclude_dirs is None:
        exclude_dirs = ['.git', '__pycache__', 'venv', 'env', 'myenv']
    
    results = {}
    
    for root, dirs, files in os.walk(directory):
        # 排除不需要搜索的目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # 搜索文件中的模式
                found_patterns = search_file_for_patterns(file_path, patterns)
                
                if found_patterns:
                    results[file_path] = found_patterns
    
    return results

def main():
    """主函数"""
    # 要搜索的目录
    search_dir = '.'
    
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
    
    # 编译正则表达式，更广泛地匹配
    patterns = []
    for folder in folder_patterns:
        # 匹配字符串中的路径
        patterns.append(re.compile(r"['\"]" + folder.replace('/', r'[/\\]') + r"['\"]"))
        # 匹配os.path.join调用
        parts = folder.split('/')
        if len(parts) > 1:
            patterns.append(re.compile(r"os\.path\.join\([^)]*['\"]" + parts[0] + r"['\"][^)]*['\"]" + parts[1] + r"['\"]"))
        # 匹配os.makedirs调用
        patterns.append(re.compile(r"os\.makedirs\([^)]*['\"]" + folder.replace('/', r'[/\\]') + r"['\"]"))
        # 匹配Path创建
        patterns.append(re.compile(r"Path\([^)]*['\"]" + folder.replace('/', r'[/\\]') + r"['\"]"))
    
    # 搜索目录
    results = search_directory(search_dir, patterns)
    
    # 打印结果
    if results:
        print("找到以下文件中可能创建文件夹的代码:")
        for file_path, found_patterns in results.items():
            print(f"\n文件: {file_path}")
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
                # 查找匹配的行
                for i, line in enumerate(lines):
                    for pattern in found_patterns:
                        if pattern.search(line):
                            # 打印上下文
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            print(f"\n行 {i+1}:")
                            for j in range(start, end):
                                if j == i:
                                    print(f">>> {lines[j].rstrip()}")
                                else:
                                    print(f"    {lines[j].rstrip()}")
    else:
        print("未找到可能创建文件夹的代码")

if __name__ == "__main__":
    main() 