FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 复制全部源码
COPY . .

# 创建日志目录
RUN mkdir -p /app/logs

# 对外暴露端口
EXPOSE 8000

# 启动命令：直接运行内置调度器和API服务
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]