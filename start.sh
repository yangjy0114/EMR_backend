#!/bin/bash
# 初始化数据库
python create_database.py
python init_db.py

# 使用 gunicorn 启动应用
gunicorn --bind 0.0.0.0:5000 app:app 