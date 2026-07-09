"""Gunicorn WSGI 入口

启动命令:
  gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
"""
from app import app

if __name__ == "__main__":
    app.run()
