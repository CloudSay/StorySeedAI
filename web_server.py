#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小说生成系统 - Web服务器
提供API接口对接前端，实现模版管理和小说生成功能
"""

import os
import sys
from api import create_app

if __name__ == '__main__':
    print("🎭 小说生成系统 Web服务器启动中...")
    print(f"📁 模版目录: {os.path.abspath('./templates')}")
    print(f"🌐 Web目录: {os.path.abspath('./web')}")
    print(f"📚 小说输出目录: {os.path.abspath('./xiaoshuo')}")
    print("🚀 服务器地址: http://localhost:5000")
    print("=" * 50)
    
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )