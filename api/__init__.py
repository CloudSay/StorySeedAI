"""
API包初始化文件
"""

from flask import Flask
import os
import sys
from flask_cors import CORS

# 全局配置
if getattr(sys, 'frozen', False):
    WEB_DIR = os.path.join(os.path.dirname(sys.executable), 'web')
else:
    WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'web')
TEMPLATES_DIR = "./templates"
XIAOSHUO_DIR = "./xiaoshuo"

# 确保目录存在
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(WEB_DIR, exist_ok=True)
os.makedirs(XIAOSHUO_DIR, exist_ok=True)

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__, static_folder=WEB_DIR)
    CORS(app)
    
    # 注册蓝图
    from .routes import static_bp, templates_bp, novels_bp, settings_bp, enhance_bp
    
    app.register_blueprint(static_bp)
    app.register_blueprint(templates_bp, url_prefix='/api')
    app.register_blueprint(novels_bp, url_prefix='/api')
    app.register_blueprint(settings_bp, url_prefix='/api')
    app.register_blueprint(enhance_bp, url_prefix='/api')
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "接口不存在"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "服务器内部错误"}, 500
    
    return app