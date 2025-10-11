"""
路由包初始化文件
"""

from flask import Blueprint

# 创建蓝图
static_bp = Blueprint('static', __name__)
templates_bp = Blueprint('templates', __name__)
novels_bp = Blueprint('novels', __name__)
settings_bp = Blueprint('settings', __name__)
enhance_bp = Blueprint('enhance', __name__)

# 导入路由模块
from . import static
from . import templates
from . import novels
from . import settings
from . import enhance