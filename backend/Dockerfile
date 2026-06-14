FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir gunicorn flasgger flask-cors sentry-sdk flask-limiter marshmallow python-dotenv \
    && pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建上传目录
RUN mkdir -p uploads/{avatars,albums,site_photos,voice}

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-", "--max-requests", "10000", "--timeout", "120", "wsgi:app"]
