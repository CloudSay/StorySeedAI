import os
import json
from typing import Dict, Any, Optional
from .data_models import ChapterState

class StateManager:
    """状态管理器 - 负责管理小说的状态信息"""
    
    def __init__(self, state_dir: str = "./data/states"):
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)
    
    def save_state(self, state: ChapterState, novel_id: Optional[str] = None) -> bool:
        """保存状态
        
        Args:
            state: 状态对象
            novel_id: 小说ID，如果为None则使用state.novel_id
            
        Returns:
            保存是否成功
        """
        try:
            if novel_id is None:
                novel_id = state.novel_id
            
            if not novel_id:
                return False
                
            state_file = os.path.join(self.state_dir, f"{novel_id}_state.json")
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state.model_dump(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存状态失败: {e}")
            return False
    
    def load_state(self, novel_id: str, chapter_index: Optional[int] = None) -> Optional[ChapterState]:
        """加载状态
        
        Args:
            novel_id: 小说ID
            chapter_index: 章节索引，如果为None则加载最新状态
            
        Returns:
            状态对象或None
        """
        try:
            state_file = os.path.join(self.state_dir, f"{novel_id}_state.json")
            if not os.path.exists(state_file):
                return None
                
            with open(state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            state = ChapterState(**state_data)
            
            # 如果指定了章节索引，更新当前章节
            if chapter_index is not None:
                state.current_chapter = chapter_index
                
            return state
        except Exception as e:
            print(f"加载状态失败: {e}")
            return None
    
    def load_latest_state(self, novel_id: Optional[str] = None) -> Optional[ChapterState]:
        """加载最新状态
        
        Args:
            novel_id: 小说ID
            
        Returns:
            状态对象或None
        """
        if novel_id is None:
            # 如果没有指定小说ID，尝试找到最新的状态文件
            state_files = [f for f in os.listdir(self.state_dir) if f.endswith('_state.json')]
            if not state_files:
                return None
            
            # 按修改时间排序，获取最新的状态文件
            state_files.sort(key=lambda f: os.path.getmtime(os.path.join(self.state_dir, f)), reverse=True)
            latest_file = state_files[0]
            novel_id = latest_file.replace('_state.json', '')
        
        return self.load_state(novel_id)
    
    def load_world_bible(self, novel_id: str) -> Optional[Dict[str, Any]]:
        """加载世界设定
        
        Args:
            novel_id: 小说ID
            
        Returns:
            世界设定字典或None
        """
        try:
            bible_file = os.path.join(self.state_dir, f"{novel_id}_bible.json")
            if not os.path.exists(bible_file):
                return None
                
            with open(bible_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载世界设定失败: {e}")
            return None
    
    def save_world_bible(self, bible: Dict[str, Any], novel_id: str) -> bool:
        """保存世界设定
        
        Args:
            bible: 世界设定字典
            novel_id: 小说ID
            
        Returns:
            保存是否成功
        """
        try:
            bible_file = os.path.join(self.state_dir, f"{novel_id}_bible.json")
            with open(bible_file, 'w', encoding='utf-8') as f:
                json.dump(bible, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存世界设定失败: {e}")
            return False