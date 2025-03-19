FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制应用文件
COPY requirements.txt .
COPY . .

# 创建必要的目录
RUN mkdir -p uploads/segmented

# 安装 Python 依赖
RUN pip3 install -r requirements.txt

# 暴露端口
EXPOSE 5000

# 运行应用
CMD ["./start.sh"] 