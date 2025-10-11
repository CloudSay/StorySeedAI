"""
静态文件服务路由
"""

import os
from flask import send_from_directory
from . import static_bp
from .. import WEB_DIR

@static_bp.route('/')
def index():
    """主页"""
    return send_from_directory(WEB_DIR, 'index.html')

@static_bp.route('/<path:filename>')
def static_files(filename):
    """静态文件服务"""
    return send_from_directory(WEB_DIR, filename)

@static_bp.route('/api/health')
def health_check():
    """健康检查"""
    return {"status": "ok", "message": "API服务正常"}