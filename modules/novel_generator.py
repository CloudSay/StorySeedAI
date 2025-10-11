import os
import json
import time
import re
from typing import List, Dict, Any, Optional

# 导入必要的模块
from .data_models import ChapterState
from .state_manager import StateManager
from .memory_manager import MemoryManager
from .llm_manager import LLMCaller
from .enhanced_features import enhancer, PlotPlanner

class NovelGenerator:
    """小说生成器 - 整合状态管理、记忆管理和增强功能"""
    
    def __init__(self, chunk_size: int = 100):
        self.state_manager = StateManager()
        self.memory_manager = MemoryManager(chunk_size=chunk_size)

    def generate_chapter(
        self,
        chapter_outline: str,
        model_name: str = "deepseek_chat",
        system_prompt: str = "",
        session_id: str = "default",
        use_state: bool = True,
        use_world_bible: bool = True,
        update_state: bool = False,
        update_model_name: Optional[str] = None,
        novel_id: Optional[str] = None,
        use_previous_chapters: bool = False,
        previous_chapters_count: int = 1
    ) -> str:
        """生成章节内容
        
        Args:
            chapter_outline: 章节细纲
            model_name: 使用的模型名称
            system_prompt: 系统提示词
            session_id: 会话ID
            use_state: 是否使用状态
            use_world_bible: 是否使用世界设定
            update_state: 是否更新状态
            update_model_name: 状态更新使用的模型
            novel_id: 小说ID
            use_previous_chapters: 是否使用前面章节内容
            previous_chapters_count: 前面章节数量
            
        Returns:
            生成的章节内容
        """
        messages = []
        
        # 添加系统提示
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 构建用户输入 - 使用更自然的提示词表达
        user_content = f"请根据下面的章节细纲进行小说内容创作：\n\n{chapter_outline}"
        
        # 加载前面章节内容
        if use_previous_chapters:
            current_chapter_index = self._extract_chapter_index(chapter_outline)
            if current_chapter_index is not None and current_chapter_index > 1:
                # 确保count在合理范围内
                count = max(1, min(previous_chapters_count, current_chapter_index - 1))
                previous_content = self.load_previous_chapters(
                    current_chapter_index, count, novel_id
                )
                if previous_content:
                    user_content += f"\n\n前面章节内容参考：\n{previous_content}"
        
        if use_state:
            state = self.state_manager.load_latest_state(novel_id)
            if state:
                user_content += f"\n\n当前状态：{state.model_dump_json(indent=2)}"
        
        if use_world_bible:
            world_bible = self.state_manager.load_world_bible(novel_id)
            if world_bible:
                user_content += f"\n\n世界设定：{json.dumps(world_bible, ensure_ascii=False, indent=2)}"
        
        user_message = {"role": "user", "content": user_content}
        messages.append(user_message)
        
        # 调用LLM
        response = LLMCaller.call(messages, model_name)
        
        # 保存章节内容 - 尝试从细纲中提取章节索引
        chapter_index = self._extract_chapter_index(chapter_outline)
        if chapter_index is not None:
            self._save_chapter(response, chapter_index, novel_id)
        
        # 状态更新 - 如果启用状态更新且使用了状态
        if update_state and use_state:
            current_state = self.state_manager.load_latest_state(novel_id)
            if current_state:
                print(f"正在更新状态...")
                try:
                    # 读取状态更新规则
                    update_rules_file = os.path.join("./prompts", "update_state_rules.txt")
                    update_system_prompt = ""
                    if os.path.exists(update_rules_file):
                        with open(update_rules_file, 'r', encoding='utf-8') as f:
                            update_system_prompt = f.read().strip()
                    
                    # 调用状态更新
                    update_model = update_model_name or model_name
                    new_state = self.update_state(
                        chapter_content=response,
                        current_state=current_state,
                        model_name=update_model,
                        novel_id=novel_id,
                        system_prompt=update_system_prompt
                    )
                    print(f"状态更新完成，新状态已保存")
                except Exception as e:
                    print(f"状态更新失败: {e}")
        
        return response

    def update_state(
        self,
        chapter_content: str,
        current_state: ChapterState,
        model_name: str = "deepseek_chat",
        novel_id: Optional[str] = None,
        system_prompt: str = """
你是一个精确的数据分析助手。你的任务是比较一个旧的JSON状态和一段新的小说章节内容，然后生成一个更新后的JSON对象。
**规则:**
1.  **以旧JSON为基础**: 完全基于我提供的旧JSON状态进行修改。
2.  **从新章节提取变化**: 阅读新的小说章节，找出所有导致状态变化的事件，例如：主角等级、属性提升；获得或失去了新物品；学会了新技能或功法；人际关系发生变化；解锁了新的任务或目标。
3.  **更新数值与描述**: 精确地更新JSON文件中的数值和描述文字。例如，"level"字段要根据小说内容合理提升。
4.  **添加新条目**: 如果有新物品或新人物关系，就在对应的数组中添加新的对象。
5.  **更新剧情总结**: 修改 `current_plot_summary` 字段，简要概括本章发生的核心事件。
6.  **严格遵守格式**: 你的输出必须严格遵循下面提供的JSON格式，不包含任何解释性文字或代码块标记。
"""
    ) -> ChapterState:
        """更新状态
        
        Args:
            chapter_content: 章节内容
            current_state: 当前状态
            model_name: 使用的模型
            novel_id: 小说ID
            system_prompt: 系统提示词
            
        Returns:
            更新后的状态
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        user_content = f"""
---
### **旧的状态JSON**：{current_state.model_dump_json(indent=2)}
---

### **本章小说内容**：{chapter_content}

---
请根据以上信息，生成更新后的JSON对象：
"""
        messages.append({"role": "user", "content": user_content})
        
        response = LLMCaller.call(messages, model_name)
        
        try:
            # 提取JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                state_data = json.loads(json_match.group())
                new_state = ChapterState(**state_data)
                self.state_manager.save_state(new_state, novel_id)
                return new_state
        except Exception as e:
            print(f"状态更新失败: {e}")
        
        return current_state

    def chat(
        self,
        user_input: str,
        model_name: str = "deepseek_chat",
        system_prompt: str = "",
        session_id: str = "default",
        use_memory: bool = True,
        recent_count: int = 20,
        use_compression: bool = False,
        compression_model: str = "deepseek_chat",
        save_conversation: bool = True
    ) -> str:
        """聊天交互
        
        Args:
            user_input: 用户输入
            model_name: 使用的模型
            system_prompt: 系统提示词
            session_id: 会话ID
            use_memory: 是否使用记忆
            recent_count: 最近消息数量
            use_compression: 是否使用压缩
            compression_model: 压缩模型
            save_conversation: 是否保存对话
            
        Returns:
            AI回复
        """
        messages = []
        
        # 添加系统提示
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 加载历史记录
        if use_memory and recent_count > 0:
            history_messages = self.memory_manager.load_recent_messages(
                session_id=session_id,
                count=recent_count,
                use_compression=use_compression,
                compression_model=compression_model
            )
            messages.extend(history_messages)
        
        # 添加当前用户输入
        user_message = {"role": "user", "content": user_input}
        messages.append(user_message)
        
        # 保存用户消息
        if save_conversation:
            self.memory_manager.save_message(session_id, user_message)
        
        # 调用LLM
        response = LLMCaller.call(messages, model_name)
        
        # 保存AI回复
        if save_conversation:
            ai_message = {"role": "assistant", "content": response}
            self.memory_manager.save_message(session_id, ai_message)
        
        return response

    def load_memory_by_range(
        self,
        session_id: str,
        start_msg: int = 1,
        end_msg: Optional[int] = None,
        use_compression: bool = False,
        compression_model: str = "deepseek_chat"
    ) -> List[Dict[str, Any]]:
        """按范围加载记忆"""
        return self.memory_manager.load_messages_by_range(
            session_id=session_id,
            start_msg=start_msg,
            end_msg=end_msg,
            use_compression=use_compression,
            compression_model=compression_model
        )
    
    def compress_memory_chunk(
        self,
        session_id: str,
        chunk_index: int,
        model_name: str = "deepseek_chat",
        compression_prompt: str = ""
    ) -> bool:
        """压缩指定的记忆分片"""
        return self.memory_manager.compress_chunk(
            session_id=session_id,
            chunk_index=chunk_index,
            model_name=model_name,
            compression_prompt=compression_prompt
        )
    
    def batch_compress_memory(
        self,
        session_id: str,
        chunk_indices: List[int],
        model_name: str = "deepseek_chat",
        compression_prompt: str = ""
    ) -> Dict[int, bool]:
        """批量压缩记忆分片"""
        return self.memory_manager.batch_compress_chunks(
            session_id=session_id,
            chunk_indices=chunk_indices,
            model_name=model_name,
            compression_prompt=compression_prompt
        )
    
    def get_memory_stats(self, session_id: str) -> Dict[str, Any]:
        """获取记忆统计信息"""
        return self.memory_manager.get_session_stats(session_id)

    def load_previous_chapters(
        self, 
        current_chapter_index: int, 
        count: int = 1, 
        novel_id: Optional[str] = None
    ) -> str:
        """加载前面章节内容
        
        Args:
            current_chapter_index: 当前章节索引
            count: 要读取的前面章节数量
            novel_id: 小说ID
            
        Returns:
            前面章节的内容字符串，如果没有则返回空字符串
        """
        if current_chapter_index <= 1 or count <= 0:
            return ""
        
        os.makedirs("./xiaoshuo", exist_ok=True)
        previous_contents = []
        
        # 从当前章节往前读取指定数量的章节
        start_index = max(1, current_chapter_index - count)
        for chapter_idx in range(start_index, current_chapter_index):
            try:
                if novel_id:
                    file_path = f"./xiaoshuo/{novel_id}_chapter_{chapter_idx:03d}.txt"
                else:
                    file_path = f"./xiaoshuo/chapter_{chapter_idx:03d}.txt"
                
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            previous_contents.append(f"【第{chapter_idx}章内容】\n{content}")
            except Exception as e:
                print(f"读取第{chapter_idx}章失败: {e}")
                continue
        
        if previous_contents:
            return "\n\n".join(previous_contents)
        return ""

    def _extract_chapter_index(self, chapter_outline: str) -> Optional[int]:
        """从章节细纲中提取章节索引"""
        # 尝试匹配各种章节索引格式
        patterns = [
            r'第(\d+)章',  # 第1章、第10章
            r'chapter[_\s]*(\d+)',  # chapter_1, chapter 1
            r'章节[_\s]*(\d+)',  # 章节_1, 章节 1
            r'【第(\d+)章',  # 【第1章
        ]
        
        for pattern in patterns:
            match = re.search(pattern, chapter_outline, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        # 如果没有找到，返回None
        return None

    def _save_chapter(self, content: str, chapter_index: int, novel_id: Optional[str] = None):
        """保存章节内容"""
        os.makedirs("./xiaoshuo", exist_ok=True)
        if novel_id:
            file_path = f"./xiaoshuo/{novel_id}_chapter_{chapter_index:03d}.txt"
        else:
            # 兼容旧格式
            file_path = f"./xiaoshuo/chapter_{chapter_index:03d}.txt"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _save_versions(self, versions: List[str], chapter_index: int, novel_id: Optional[str] = None):
        """保存版本信息"""
        os.makedirs("./versions", exist_ok=True)
        if novel_id:
            file_path = f"./versions/{novel_id}_chapter_{chapter_index}_versions.json"
        else:
            # 兼容旧格式
            file_path = f"./versions/chapter_{chapter_index}_versions.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                "novel_id": novel_id,
                "chapter_index": chapter_index,
                "versions": versions,
                "created_at": time.time()
            }, f, indent=2, ensure_ascii=False)

    def generate_enhanced_chapter(self, novel_id: str, chapter_number: int, prompt: str, 
                                enhancement_options: Dict[str, Any], update_state: bool = False, 
                                model_name: str = "deepseek_chat") -> Dict[str, Any]:
        """生成并增强章节内容"""
        # 1. 生成原始章节内容
        chapter_content = self.generate_chapter(
            novel_id, chapter_number, prompt, update_state=False, model_name=model_name
        )
        
        # 2. 增强章节内容
        enhanced_result = enhancer.enhance_chapter(
            chapter_content, enhancement_options, model_name
        )
        
        # 3. 保存增强后的内容
        final_content = enhanced_result["final_content"]
        self._save_chapter(final_content, chapter_number, novel_id)
        
        # 4. 更新状态（如果需要）
        if update_state:
            current_state = self.state_manager.load_latest_state(novel_id)
            if current_state:
                self.update_state(
                    chapter_content=final_content,
                    current_state=current_state,
                    model_name=model_name,
                    novel_id=novel_id
                )
        
        return {
            "chapter_content": final_content,
            "enhancement_details": enhanced_result
        }
    
    def generate_chapter_outline(self, novel_id: str, current_chapter: int, model_name: str = "deepseek_chat") -> str:
        """生成章节大纲"""
        # 获取世界设定
        world_bible = self.state_manager.load_world_bible(novel_id)
        
        # 获取当前状态
        current_state = self.state_manager.load_latest_state(novel_id)
        
        # 获取前几章内容
        previous_content = ""
        if current_chapter > 0:
            for i in range(max(0, current_chapter - 3), current_chapter):
                if novel_id:
                    file_path = f"./xiaoshuo/{novel_id}_chapter_{i:03d}.txt"
                else:
                    file_path = f"./xiaoshuo/chapter_{i:03d}.txt"
                
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        previous_content += f.read() + "\n\n"
        
        # 生成大纲
        return PlotPlanner.generate_chapter_outline(
            novel_id, current_chapter, world_bible, current_state, previous_content, model_name
        )
    
    def generate_story_arc(self, novel_id: str, model_name: str = "deepseek_chat") -> Dict[str, Any]:
        """生成故事弧线规划"""
        # 获取世界设定
        world_bible = self.state_manager.load_world_bible(novel_id)
        
        # 获取主角设定
        protagonist_profile = {}
        character_settings = self.state_manager.load_character_settings(novel_id)
        if character_settings and "protagonist" in character_settings:
            protagonist_profile = character_settings["protagonist"]
        
        # 生成故事弧线
        return PlotPlanner.generate_story_arc(
            novel_id, world_bible, protagonist_profile, model_name
        )