import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db

def list_all_tables():
    """列出数据库中的所有表及其结构"""
    with app.app_context():
        try:
            # 使用text()函数包装SQL语句
            from sqlalchemy import text
            
            # 获取所有表名
            result = db.session.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"数据库中共有 {len(tables)} 个表:")
            
            # 遍历每个表，显示其结构
            for table in tables:
                print(f"\n表名: {table}")
                print("-" * 80)
                
                # 获取表结构
                result = db.session.execute(text(f"DESCRIBE {table}"))
                columns = result.fetchall()
                
                # 打印表头
                print(f"{'字段名':<20} {'类型':<20} {'可为空':<10} {'键':<10} {'默认值':<20} {'额外信息':<20}")
                print("-" * 80)
                
                # 打印每一列
                for column in columns:
                    field = column[0] if column[0] else ""
                    type_ = column[1] if column[1] else ""
                    null = column[2] if column[2] else ""
                    key = column[3] if column[3] else ""
                    default = str(column[4]) if column[4] is not None else "NULL"
                    extra = column[5] if column[5] else ""
                    
                    print(f"{field:<20} {type_:<20} {null:<10} {key:<10} {default:<20} {extra:<20}")
                
                # 获取外键约束
                try:
                    result = db.session.execute(text(f"""
                        SELECT 
                            COLUMN_NAME, 
                            REFERENCED_TABLE_NAME, 
                            REFERENCED_COLUMN_NAME 
                        FROM 
                            INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                        WHERE 
                            TABLE_NAME = '{table}' 
                            AND REFERENCED_TABLE_NAME IS NOT NULL
                    """))
                    foreign_keys = result.fetchall()
                    
                    if foreign_keys:
                        print("\n外键约束:")
                        print(f"{'列名':<20} {'引用表':<20} {'引用列':<20}")
                        print("-" * 60)
                        
                        for fk in foreign_keys:
                            column = fk[0] if fk[0] else ""
                            ref_table = fk[1] if fk[1] else ""
                            ref_column = fk[2] if fk[2] else ""
                            
                            print(f"{column:<20} {ref_table:<20} {ref_column:<20}")
                except Exception as e:
                    print(f"获取外键约束时出错: {str(e)}")
                
        except Exception as e:
            print(f"查询数据库结构时出错: {str(e)}")
            db.session.rollback()

def count_records_in_tables():
    """统计每个表中的记录数"""
    with app.app_context():
        try:
            # 使用text()函数包装SQL语句
            from sqlalchemy import text
            
            # 获取所有表名
            result = db.session.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"\n各表记录数:")
            print("-" * 40)
            print(f"{'表名':<30} {'记录数':<10}")
            print("-" * 40)
            
            # 遍历每个表，统计记录数
            for table in tables:
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                
                print(f"{table:<30} {count:<10}")
                
        except Exception as e:
            print(f"统计记录数时出错: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    list_all_tables()
    count_records_in_tables() 