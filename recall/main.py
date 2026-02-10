"""
Recall - 屏幕截图记录工具
Windows Recall 的本地开源替代品

启动方式: python main.py
访问地址: http://127.0.0.1:5000
"""
from app import RecallApp


def main():
    app = RecallApp()
    app.run()


if __name__ == "__main__":
    main()
