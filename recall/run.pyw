"""
Recall - 无窗口启动入口
双击此文件启动应用，不会显示命令行窗口
"""
import sys
import os

# 确保工作目录正确
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import RecallApp

if __name__ == "__main__":
    app = RecallApp()
    app.run()
