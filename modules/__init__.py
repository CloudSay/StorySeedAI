# 小说生成系统模块包
"""
此包包含小说生成系统的各个核心模块组件。
"""

# 从各个模块导入主要类和函数
from .data_models import ChapterState, Relationship, InventoryItem, Protagonist
from .llm_manager import LLMConfigManager, LLMCaller
from .state_manager import StateManager
from .memory_manager import MemoryManager
from .novel_generator import NovelGenerator
from .enhanced_features import ContentModerator, DialogueOptimizer, StyleTransfer, PlotPlanner, NovelEnhancer

__all__ = [
    # 数据模型
    'ChapterState', 'Relationship', 'InventoryItem', 'Protagonist',
    # LLM管理
    'LLMConfigManager', 'LLMCaller',
    # 状态管理
    'StateManager',
    # 记忆管理
    'MemoryManager',
    # 小说生成
    'NovelGenerator',
    # 增强功能
    'ContentModerator', 'DialogueOptimizer', 'StyleTransfer', 'PlotPlanner', 'NovelEnhancer'
]

__version__ = '1.0.0'