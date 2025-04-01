#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库设计信息收集脚本
用于收集眼科智能诊断系统的数据库设计信息，包括表结构、关系、索引等
"""

import os
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine, inspect, MetaData, Table, text
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目配置
try:
    from app import app
    from models import db
    DATABASE_URL = app.config['SQLALCHEMY_DATABASE_URI']
except ImportError:
    # 如果无法导入项目配置，使用默认配置
    DATABASE_URL = 'mysql+mysqlconnector://root:59fh8r22@test-db-mysql.ns-32fwr7d7.svc:3306/test_db'

# 创建数据库连接
engine = create_engine(DATABASE_URL)
inspector = inspect(engine)
metadata = MetaData()
metadata.reflect(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()

def get_table_info():
    """获取所有表的信息"""
    tables_info = []
    
    # 获取所有表名
    table_names = inspector.get_table_names()
    
    for table_name in table_names:
        # 获取主键信息
        pk_constraint = inspector.get_pk_constraint(table_name)
        primary_keys = pk_constraint.get('constrained_columns', []) if pk_constraint else []
        
        table_info = {
            'name': table_name,
            'columns': [],
            'primary_keys': primary_keys,
            'foreign_keys': [],
            'indexes': inspector.get_indexes(table_name),
            'row_count': get_row_count(table_name)
        }
        
        # 获取列信息
        columns = inspector.get_columns(table_name)
        for column in columns:
            column_info = {
                'name': column['name'],
                'type': str(column['type']),
                'nullable': column['nullable'],
                'default': str(column.get('default', 'None')),
                'primary_key': column['name'] in primary_keys
            }
            table_info['columns'].append(column_info)
        
        # 获取外键信息
        foreign_keys = inspector.get_foreign_keys(table_name)
        for fk in foreign_keys:
            fk_info = {
                'constrained_columns': fk['constrained_columns'],
                'referred_table': fk['referred_table'],
                'referred_columns': fk['referred_columns']
            }
            table_info['foreign_keys'].append(fk_info)
        
        tables_info.append(table_info)
    
    return tables_info

def get_row_count(table_name):
    """获取表的行数"""
    try:
        result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        return result.scalar()
    except Exception as e:
        print(f"获取表 {table_name} 的行数时出错: {str(e)}")
        return 0

def get_table_relationships():
    """获取表之间的关系"""
    relationships = []
    
    for table_name in inspector.get_table_names():
        foreign_keys = inspector.get_foreign_keys(table_name)
        for fk in foreign_keys:
            relationship = {
                'source_table': table_name,
                'source_columns': fk['constrained_columns'],
                'target_table': fk['referred_table'],
                'target_columns': fk['referred_columns'],
                'name': fk.get('name', '')
            }
            relationships.append(relationship)
    
    return relationships

def get_database_stats():
    """获取数据库统计信息"""
    stats = {
        'table_count': len(inspector.get_table_names()),
        'tables': {}
    }
    
    for table_name in inspector.get_table_names():
        try:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            row_count = result.scalar()
            
            column_count = len(inspector.get_columns(table_name))
            index_count = len(inspector.get_indexes(table_name))
            fk_count = len(inspector.get_foreign_keys(table_name))
            
            stats['tables'][table_name] = {
                'row_count': row_count,
                'column_count': column_count,
                'index_count': index_count,
                'foreign_key_count': fk_count
            }
        except Exception as e:
            print(f"获取表 {table_name} 的统计信息时出错: {str(e)}")
    
    return stats

def get_table_creation_sql():
    """获取表的创建SQL语句"""
    creation_sql = {}
    
    for table_name in inspector.get_table_names():
        try:
            result = session.execute(text(f"SHOW CREATE TABLE {table_name}"))
            row = result.fetchone()
            if row and len(row) > 1:
                creation_sql[table_name] = row[1]
            else:
                creation_sql[table_name] = "无法获取创建SQL"
        except Exception as e:
            print(f"获取表 {table_name} 的创建SQL时出错: {str(e)}")
            creation_sql[table_name] = f"错误: {str(e)}"
    
    return creation_sql

def format_table_info(table_info):
    """格式化表信息为易读的文本"""
    output = []
    output.append(f"表名: {table_info['name']}")
    output.append(f"记录数: {table_info['row_count']}")
    output.append("-" * 100)
    
    # 格式化列信息
    column_headers = ["列名", "类型", "可空", "默认值", "主键"]
    column_data = []
    for col in table_info['columns']:
        column_data.append([
            col['name'],
            col['type'],
            "是" if col['nullable'] else "否",
            col['default'],
            "是" if col['primary_key'] else "否"
        ])
    
    # 计算每列的最大宽度
    col_widths = [max(len(str(row[i])) for row in column_data + [column_headers]) for i in range(len(column_headers))]
    
    # 打印表头
    header = " | ".join(f"{column_headers[i]:{col_widths[i]}}" for i in range(len(column_headers)))
    output.append(header)
    output.append("-" * len(header))
    
    # 打印数据行
    for row in column_data:
        output.append(" | ".join(f"{str(row[i]):{col_widths[i]}}" for i in range(len(row))))
    
    output.append("")
    
    # 打印主键信息
    if table_info['primary_keys']:
        output.append(f"主键: {', '.join(table_info['primary_keys'])}")
    
    # 打印外键信息
    if table_info['foreign_keys']:
        output.append("外键:")
        for fk in table_info['foreign_keys']:
            output.append(f"  {', '.join(fk['constrained_columns'])} -> {fk['referred_table']}({', '.join(fk['referred_columns'])})")
    
    # 打印索引信息
    if table_info['indexes']:
        output.append("索引:")
        for idx in table_info['indexes']:
            unique = "唯一" if idx['unique'] else "非唯一"
            output.append(f"  {idx['name']} ({', '.join(idx['column_names'])}) - {unique}")
    
    return "\n".join(output)

def main():
    """主函数"""
    print("=" * 100)
    print("眼科智能诊断系统数据库设计信息")
    print("=" * 100)
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库连接: {DATABASE_URL}")
    print("=" * 100)
    
    # 获取数据库信息
    tables_info = get_table_info()
    relationships = get_table_relationships()
    stats = get_database_stats()
    creation_sql = get_table_creation_sql()
    
    # 打印数据库统计信息
    print("\n数据库统计信息:")
    print(f"表数量: {stats['table_count']}")
    print("-" * 100)
    for table_name, table_stats in stats['tables'].items():
        print(f"{table_name}: {table_stats['row_count']} 行, {table_stats['column_count']} 列, {table_stats['index_count']} 个索引, {table_stats['foreign_key_count']} 个外键")
    
    # 打印表信息
    print("\n\n表结构信息:")
    for table_info in tables_info:
        print("\n" + "=" * 100)
        print(format_table_info(table_info))
    
    # 打印表关系
    print("\n\n表关系信息:")
    print("-" * 100)
    for rel in relationships:
        print(f"{rel['source_table']}({', '.join(rel['source_columns'])}) -> {rel['target_table']}({', '.join(rel['target_columns'])})")
    
    # 打印表创建SQL
    print("\n\n表创建SQL:")
    for table_name, sql in creation_sql.items():
        print("\n" + "=" * 100)
        print(f"表名: {table_name}")
        print("-" * 100)
        print(sql)
    
    # 保存到文件
    output_file = "database_design_info.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=" * 100 + "\n")
        f.write("眼科智能诊断系统数据库设计信息\n")
        f.write("=" * 100 + "\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"数据库连接: {DATABASE_URL}\n")
        f.write("=" * 100 + "\n")
        
        # 写入数据库统计信息
        f.write("\n数据库统计信息:\n")
        f.write(f"表数量: {stats['table_count']}\n")
        f.write("-" * 100 + "\n")
        for table_name, table_stats in stats['tables'].items():
            f.write(f"{table_name}: {table_stats['row_count']} 行, {table_stats['column_count']} 列, {table_stats['index_count']} 个索引, {table_stats['foreign_key_count']} 个外键\n")
        
        # 写入表信息
        f.write("\n\n表结构信息:\n")
        for table_info in tables_info:
            f.write("\n" + "=" * 100 + "\n")
            f.write(format_table_info(table_info) + "\n")
        
        # 写入表关系
        f.write("\n\n表关系信息:\n")
        f.write("-" * 100 + "\n")
        for rel in relationships:
            f.write(f"{rel['source_table']}({', '.join(rel['source_columns'])}) -> {rel['target_table']}({', '.join(rel['target_columns'])})\n")
        
        # 写入表创建SQL
        f.write("\n\n表创建SQL:\n")
        for table_name, sql in creation_sql.items():
            f.write("\n" + "=" * 100 + "\n")
            f.write(f"表名: {table_name}\n")
            f.write("-" * 100 + "\n")
            f.write(sql + "\n")
    
    print(f"\n\n信息已保存到文件: {output_file}")

if __name__ == "__main__":
    main()