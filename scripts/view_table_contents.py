import sys
import os
import json
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db

def json_serial(obj):
    """处理JSON序列化时无法处理的类型"""
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError(f"Type {type(obj)} not serializable")

def view_table_contents(table_name=None):
    """查看表中的所有数据
    
    Args:
        table_name: 要查看的表名，如果为None则查看所有表
    """
    with app.app_context():
        try:
            # 使用text()函数包装SQL语句
            from sqlalchemy import text
            
            # 获取所有表名
            if table_name:
                tables = [table_name]
            else:
                result = db.session.execute(text("SHOW TABLES"))
                tables = [row[0] for row in result.fetchall()]
            
            # 遍历每个表，显示其内容
            for table in tables:
                # 获取表结构
                result = db.session.execute(text(f"DESCRIBE {table}"))
                columns = [row[0] for row in result.fetchall()]
                
                # 获取表中的所有数据
                result = db.session.execute(text(f"SELECT * FROM {table}"))
                rows = result.fetchall()
                
                print(f"\n表名: {table}")
                print(f"记录数: {len(rows)}")
                print("-" * 100)
                
                if not rows:
                    print("表中没有数据")
                    continue
                
                # 打印表头
                header = " | ".join([f"{col:<15}" for col in columns])
                print(header)
                print("-" * 100)
                
                # 打印每一行数据
                for row in rows:
                    # 格式化每个字段的值
                    formatted_values = []
                    for value in row:
                        if value is None:
                            formatted_values.append("NULL")
                        elif isinstance(value, (int, float)):
                            formatted_values.append(str(value))
                        elif isinstance(value, datetime):
                            formatted_values.append(value.strftime('%Y-%m-%d %H:%M:%S'))
                        elif isinstance(value, (bytes, bytearray)):
                            formatted_values.append("<binary data>")
                        else:
                            # 截断过长的字符串
                            s = str(value)
                            if len(s) > 15:
                                s = s[:12] + "..."
                            formatted_values.append(s)
                    
                    # 打印行
                    row_str = " | ".join([f"{val:<15}" for val in formatted_values])
                    print(row_str)
                
                # 如果记录太多，只显示前10条和后10条
                if len(rows) > 20:
                    print("\n... 省略中间记录 ...")
                    
        except Exception as e:
            print(f"查询表内容时出错: {str(e)}")
            db.session.rollback()

def export_table_to_json(table_name):
    """将表中的数据导出为JSON文件
    
    Args:
        table_name: 要导出的表名
    """
    with app.app_context():
        try:
            # 使用text()函数包装SQL语句
            from sqlalchemy import text
            
            # 获取表结构
            result = db.session.execute(text(f"DESCRIBE {table_name}"))
            columns = [row[0] for row in result.fetchall()]
            
            # 获取表中的所有数据
            result = db.session.execute(text(f"SELECT * FROM {table_name}"))
            rows = result.fetchall()
            
            # 将数据转换为字典列表
            data = []
            for row in rows:
                item = {}
                for i, col in enumerate(columns):
                    item[col] = row[i]
                data.append(item)
            
            # 导出为JSON文件
            output_file = f"data/{table_name}.json"
            os.makedirs("data", exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, default=json_serial, indent=2, ensure_ascii=False)
            
            print(f"表 {table_name} 的数据已导出到 {output_file}")
            
        except Exception as e:
            print(f"导出表数据时出错: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        table_name = sys.argv[1]
        view_table_contents(table_name)
        
        # 如果指定了--export参数，则导出为JSON
        if len(sys.argv) > 2 and sys.argv[2] == "--export":
            export_table_to_json(table_name)
    else:
        view_table_contents() 