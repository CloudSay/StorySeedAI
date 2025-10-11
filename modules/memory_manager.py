import os
import json
import time
import glob
from typing import List, Dict, Any, Optional

class MemoryManager:
    """记忆管理器 - 负责管理对话记忆和消息存储"""
    
    def __init__(self, memory_dir: str = "./memory", chunk_size: int = 100):
        self.memory_dir = memory_dir
        self.chunk_size = chunk_size
        os.makedirs(memory_dir, exist_ok=True)
    
    def save_message(self, session_id: str, role: str, content: str) -> bool:
        """保存消息
        
        Args:
            session_id: 会话ID
            role: 角色（user/assistant/system）
            content: 消息内容
            
        Returns:
            保存是否成功
        """
        try:
            # 获取当前消息数量
            messages = self._load_session_messages(session_id)
            message_count = len(messages)
            
            # 计算所属分片
            chunk_index = message_count // self.chunk_size
            
            # 创建分片目录
            chunk_dir = os.path.join(self.memory_dir, session_id, f"chunk_{chunk_index}")
            os.makedirs(chunk_dir, exist_ok=True)
            
            # 保存消息
            message_file = os.path.join(chunk_dir, f"message_{message_count}.json")
            message_data = {
                "role": role,
                "content": content,
                "timestamp": time.time()
            }
            
            with open(message_file, 'w', encoding='utf-8') as f:
                json.dump(message_data, f, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"保存消息失败: {e}")
            return False
    
    def load_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """加载消息
        
        Args:
            session_id: 会话ID
            limit: 消息数量限制，如果为None则加载所有消息
            
        Returns:
            消息列表
        """
        try:
            messages = self._load_session_messages(session_id)
            
            if limit is not None and len(messages) > limit:
                messages = messages[-limit:]
                
            return messages
        except Exception as e:
            print(f"加载消息失败: {e}")
            return []
    
    def _load_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """加载会话的所有消息
        
        Args:
            session_id: 会话ID
            
        Returns:
            消息列表
        """
        messages = []
        session_dir = os.path.join(self.memory_dir, session_id)
        
        if not os.path.exists(session_dir):
            return messages
        
        # 获取所有分片目录
        chunk_dirs = [d for d in os.listdir(session_dir) if d.startswith("chunk_")]
        chunk_dirs.sort(key=lambda x: int(x.split("_")[1]))
        
        # 遍历所有分片
        for chunk_dir in chunk_dirs:
            chunk_path = os.path.join(session_dir, chunk_dir)
            
            # 获取分片中的所有消息文件
            message_files = glob.glob(os.path.join(chunk_path, "message_*.json"))
            message_files.sort(key=lambda x: int(os.path.basename(x).split("_")[1].split(".")[0]))
            
            # 加载消息
            for message_file in message_files:
                with open(message_file, 'r', encoding='utf-8') as f:
                    message_data = json.load(f)
                    messages.append({
                        "role": message_data["role"],
                        "content": message_data["content"]
                    })
        
        return messages
    
    def list_sessions(self) -> List[str]:
        """列出所有会话
        
        Returns:
            会话ID列表
        """
        try:
            if not os.path.exists(self.memory_dir):
                return []
            
            sessions = [d for d in os.listdir(self.memory_dir) 
                       if os.path.isdir(os.path.join(self.memory_dir, d))]
            return sessions
        except Exception as e:
            print(f"列出会话失败: {e}")
            return []
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """获取会话统计信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            统计信息字典
        """
        try:
            messages = self._load_session_messages(session_id)
            session_dir = os.path.join(self.memory_dir, session_id)
            
            # 计算分片数量
            chunk_dirs = [d for d in os.listdir(session_dir) if d.startswith("chunk_")]
            chunk_count = len(chunk_dirs)
            
            # 计算消息数量
            message_count = len(messages)
            
            # 计算最后一条消息的时间
            last_message_time = None
            if messages:
                # 从消息文件中获取时间戳
                last_chunk_dir = os.path.join(session_dir, chunk_dirs[-1]) if chunk_dirs else None
                if last_chunk_dir:
                    message_files = glob.glob(os.path.join(last_chunk_dir, "message_*.json"))
                    if message_files:
                        message_files.sort(key=lambda x: int(os.path.basename(x).split("_")[1].split(".")[0]))
                        last_message_file = message_files[-1]
                        with open(last_message_file, 'r', encoding='utf-8') as f:
                            message_data = json.load(f)
                            last_message_time = message_data.get("timestamp")
            
            return {
                "session_id": session_id,
                "message_count": message_count,
                "chunk_count": chunk_count,
                "chunk_size": self.chunk_size,
                "last_message_time": last_message_time
            }
        except Exception as e:
            print(f"获取会话统计信息失败: {e}")
            return {}