import os

def process_reports(input_file, report_type, start_range=None, end_range=None):
    """处理报告文本并保存到对应目录
    
    Args:
        input_file: 输入文件路径
        report_type: 报告类型 (amd/dme/normal)
        start_range: 开始范围（报告索引，从1开始）
        end_range: 结束范围（报告索引，包含）
    """
    # 确保目录存在
    output_dir = f"data/reports/{report_type}"
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 按分隔符分割报告
    reports = content.split('---')
    reports = [r.strip() for r in reports if r.strip()]
    
    # 如果指定了范围，则只处理该范围内的报告
    if start_range is not None and end_range is not None:
        if start_range < 1:
            start_range = 1
        if end_range > len(reports):
            end_range = len(reports)
        reports = reports[start_range-1:end_range]
    
    # 获取目录中已有的文件数量
    existing_files = [f for f in os.listdir(output_dir) if f.endswith('.txt')]
    start_index = len(existing_files) + 1
    
    # 保存每份报告
    for i, report in enumerate(reports, start=start_index):
        if not report:
            continue
            
        output_file = os.path.join(output_dir, f"{i}.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"已保存报告 {i} 到 {output_file}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3 or len(sys.argv) > 5:
        print("用法: python process_reports.py <输入文件> <报告类型> [开始范围] [结束范围]")
        print("报告类型: amd, dme, normal")
        sys.exit(1)
    
    input_file = sys.argv[1]
    report_type = sys.argv[2].lower()
    
    if report_type not in ['amd', 'dme', 'normal']:
        print("无效的报告类型。有效类型: amd, dme, normal")
        sys.exit(1)
    
    start_range = int(sys.argv[3]) if len(sys.argv) > 3 else None
    end_range = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    process_reports(input_file, report_type, start_range, end_range) 