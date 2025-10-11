import os
import json
import glob
import re
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

# === 导入模块化组件 ===
from modules.data_models import Relationship, InventoryItem, Protagonist, ChapterState
from modules.llm_manager import LLMConfigManager, LLMCaller
from modules.state_manager import StateManager
from modules.memory_manager import MemoryManager
from modules.novel_generator import NovelGenerator
from modules.enhanced_features import enhancer

# === 示例使用 ===
if __name__ == "__main__":
    # 测试架构初始化
    print("=== 小说生成系统 - 高度模块化架构 ===")
    
    # 1. 测试配置管理器
    print("\n1. 测试配置管理器:")
    config = LLMConfigManager.get_config("deepseek_chat")
    print(f"   DeepSeek Chat配置: {config['provider']}, {config['model']}")
    print(f"   Base URL: {config['base_url']}")
    config_default = LLMConfigManager.get_config("")  # 测试默认
    print(f"   默认模型: {config_default['model']}")
    
    # 2. 测试组件初始化
    print("\n2. 测试组件初始化:")
    generator = NovelGenerator(chunk_size=100)
    print("   ✓ NovelGenerator 初始化成功")
    print("   ✓ StateManager 初始化成功")
    print("   ✓ MemoryManager 初始化成功 (分片存储+压缩)")
    
    # 测试不同分片大小
    small_chunk_generator = NovelGenerator(chunk_size=50)
    print("   ✓ NovelGenerator (小分片) 初始化成功")
    
    # 3. 测试会话管理
    print("\n3. 测试会话管理:")
    sessions = generator.memory_manager.list_sessions()
    print(f"   当前会话列表: {sessions}")
    
    # 4. 显示使用示例
    print("\n4. 使用示例:")
    print("   # 生成章节")
    print("   generator.generate_chapter(chapter_plan, use_state=True, use_world_bible=True)")
    print("   # 命令行交互")
    print("   generator.chat('继续写作')")
    print("   # 读取前面章节内容")
    print("   generator.load_previous_chapters(3, 2, 'novel_001')")
    print("   # 直接调用LLM")
    print("   LLMCaller.call(messages, model_name='dsf5')")
    
    print("\n=== 架构测试完成 ===")
    print("所有组件已成功初始化，可以开始使用！")