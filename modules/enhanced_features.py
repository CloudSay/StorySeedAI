import json
import re
from typing import List, Dict, Any, Optional
import time

# 导入主模块中的必要组件
from main import LLMCaller, ChapterState

class ContentModerator:
    """内容审查与过滤系统"""
    @staticmethod
    def moderate_content(content: str, model_name: str = "deepseek_chat") -> Dict[str, Any]:
        """审查内容并提供修改建议"""
        messages = [
            {"role": "system", "content": "你是一位内容审查专家，负责检查文本是否符合出版规范。"}
        ]
        
        user_content = f"""
        请审查以下内容，检查是否包含敏感信息、不当言论或不符合出版规范的内容：
        
        {content}
        
        请提供详细的审查报告，指出问题所在并给出修改建议。
        如果内容没有问题，请明确说明。
        """
        
        messages.append({"role": "user", "content": user_content})
        
        result = LLMCaller.call(messages, model_name)
        
        return {
            "original_content": content,
            "moderation_result": result,
            "has_issues": "没有问题" not in result and "不存在问题" not in result,
            "timestamp": time.time()
        }

class DialogueOptimizer:
    """角色对话优化器"""
    @staticmethod
    def optimize_dialogue(dialogue: str, character_profiles: Dict[str, Dict[str, Any]], model_name: str = "deepseek_chat") -> str:
        """根据角色设定优化对话内容"""
        messages = [
            {"role": "system", "content": "你是一位对话编辑专家，擅长根据角色设定优化对话内容，使其更符合角色性格和背景。"}
        ]
        
        user_content = f"""
        请根据以下角色设定，优化对话内容，确保每个角色的语言风格都符合其性格特点：
        
        角色设定：
        {json.dumps(character_profiles, ensure_ascii=False, indent=2)}
        
        需要优化的对话：
        {dialogue}
        
        优化要求：
        1. 保持对话原意不变
        2. 调整语言风格以符合角色设定
        3. 保留必要的对话标签（如"XXX说："）
        """
        
        messages.append({"role": "user", "content": user_content})
        
        return LLMCaller.call(messages, model_name)

class StyleTransfer:
    """风格迁移功能"""
    @staticmethod
    def transfer_style(content: str, style_prompt: str, model_name: str = "deepseek_chat") -> str:
        """将内容转换为指定风格"""
        messages = [
            {"role": "system", "content": "你是一位多才多艺的作家，能够模仿各种文学风格进行创作。"}
        ]
        
        user_content = f"""
        请将以下内容转换为指定风格：
        
        目标风格：
        {style_prompt}
        
        原始内容：
        {content}
        
        转换要求：
        1. 保持内容原意不变
        2. 调整语言风格以符合目标风格
        3. 保持内容结构和关键信息
        """
        
        messages.append({"role": "user", "content": user_content})
        
        return LLMCaller.call(messages, model_name)

class PlotPlanner:
    """自动情节规划器"""
    @staticmethod
    def generate_chapter_outline(novel_id: str, current_chapter: int, world_bible: Dict[str, Any], 
                               current_state: ChapterState, previous_content: str, 
                               model_name: str = "deepseek_chat") -> str:
        """自动生成章节大纲"""
        messages = [
            {"role": "system", "content": "你是一位优秀的小说策划师，擅长根据现有剧情发展生成下一章的详细大纲。"}
        ]
        
        user_content = f"""
        请根据以下信息，为小说生成第{current_chapter + 1}章的详细大纲：
        
        世界设定：{json.dumps(world_bible, ensure_ascii=False) if world_bible else "无"}
        
        当前状态：{current_state.model_dump_json(ensure_ascii=False) if current_state else "无"}
        
        前几章内容：{previous_content if previous_content else "无"}
        
        请生成包含场景、冲突、角色发展等要素的详细大纲，约300-500字。
        """
        
        messages.append({"role": "user", "content": user_content})
        
        return LLMCaller.call(messages, model_name)

    @staticmethod
    def generate_story_arc(novel_id: str, world_bible: Dict[str, Any], 
                          protagonist_profile: Dict[str, Any], 
                          model_name: str = "deepseek_chat") -> Dict[str, Any]:
        """生成完整的故事弧线规划"""
        messages = [
            {"role": "system", "content": "你是一位资深的故事架构师，擅长设计完整的小说故事弧线。"}
        ]
        
        user_content = f"""
        请根据以下信息，为小说设计一个完整的故事弧线：
        
        世界设定：{json.dumps(world_bible, ensure_ascii=False) if world_bible else "无"}
        
        主角设定：{json.dumps(protagonist_profile, ensure_ascii=False) if protagonist_profile else "无"}
        
        请设计包括以下要素的故事弧线：
        1. 故事梗概（约200字）
        2. 主要情节节点（至少5个关键转折点）
        3. 章节规划（建议的总章节数和每章主要内容概述）
        4. 角色成长弧线
        5. 主题和核心冲突
        """
        
        messages.append({"role": "user", "content": user_content})
        
        result = LLMCaller.call(messages, model_name)
        
        # 尝试解析结果为结构化数据
        try:
            # 提取各个部分
            summary_match = re.search(r'故事梗概[：:](.*?)(主要情节节点|章节规划|角色成长弧线|主题和核心冲突)', result, re.DOTALL)
            plot_nodes_match = re.search(r'主要情节节点[：:](.*?)(章节规划|角色成长弧线|主题和核心冲突)', result, re.DOTALL)
            chapter_plan_match = re.search(r'章节规划[：:](.*?)(角色成长弧线|主题和核心冲突)', result, re.DOTALL)
            character_arc_match = re.search(r'角色成长弧线[：:](.*?)(主题和核心冲突)', result, re.DOTALL)
            themes_conflicts_match = re.search(r'主题和核心冲突[：:](.*)', result, re.DOTALL)
            
            return {
                "novel_id": novel_id,
                "story_summary": summary_match.group(1).strip() if summary_match else "",
                "plot_nodes": plot_nodes_match.group(1).strip() if plot_nodes_match else "",
                "chapter_plan": chapter_plan_match.group(1).strip() if chapter_plan_match else "",
                "character_arc": character_arc_match.group(1).strip() if character_arc_match else "",
                "themes_conflicts": themes_conflicts_match.group(1).strip() if themes_conflicts_match else "",
                "raw_result": result,
                "generated_at": time.time()
            }
        except:
            # 如果解析失败，返回原始结果
            return {
                "novel_id": novel_id,
                "raw_result": result,
                "generated_at": time.time(),
                "parse_error": True
            }

class NovelEnhancer:
    """小说增强主类，整合所有增强功能"""
    def __init__(self):
        self.moderator = ContentModerator()
        self.dialogue_optimizer = DialogueOptimizer()
        self.style_transfer = StyleTransfer()
        self.plot_planner = PlotPlanner()

    def enhance_chapter(self, content: str, enhancement_options: Dict[str, Any], 
                       model_name: str = "deepseek_chat") -> Dict[str, Any]:
        """综合增强章节内容"""
        result = {
            "original_content": content,
            "enhancements": {},
            "timestamp": time.time()
        }
        
        # 内容审查
        if enhancement_options.get("moderate_content", False):
            moderation_result = self.moderator.moderate_content(content, model_name)
            result["enhancements"]["moderation"] = moderation_result
            
            # 如果有问题且选择自动修正
            if moderation_result["has_issues"] and enhancement_options.get("auto_fix_issues", False):
                fixed_content = self._auto_fix_content(content, moderation_result["moderation_result"], model_name)
                result["enhancements"]["fixed_content"] = fixed_content
                content = fixed_content
        
        # 对话优化
        if enhancement_options.get("optimize_dialogue", False) and enhancement_options.get("character_profiles"):
            optimized_dialogue = self.dialogue_optimizer.optimize_dialogue(
                content, enhancement_options["character_profiles"], model_name
            )
            result["enhancements"]["dialogue_optimization"] = optimized_dialogue
            content = optimized_dialogue
        
        # 风格迁移
        if enhancement_options.get("transfer_style", False) and enhancement_options.get("style_prompt"):
            styled_content = self.style_transfer.transfer_style(
                content, enhancement_options["style_prompt"], model_name
            )
            result["enhancements"]["style_transfer"] = styled_content
            content = styled_content
        
        # 润色
        if enhancement_options.get("polish_content", False):
            polished_content = self._polish_content(content, model_name)
            result["enhancements"]["polished_content"] = polished_content
            content = polished_content
        
        result["final_content"] = content
        return result
    
    def _auto_fix_content(self, content: str, moderation_result: str, model_name: str = "deepseek_chat") -> str:
        """根据审查结果自动修正内容"""
        messages = [
            {"role": "system", "content": "你是一位内容编辑专家，擅长根据审查意见修正文本内容。"}
        ]
        
        user_content = f"""
        请根据以下审查结果修正内容，确保修正后的内容符合出版规范：
        
        审查结果：
        {moderation_result}
        
        需要修正的内容：
        {content}
        
        修正要求：
        1. 完全解决审查结果中指出的问题
        2. 保持内容原意不变
        3. 确保语言流畅自然
        """
        
        messages.append({"role": "user", "content": user_content})
        
        return LLMCaller.call(messages, model_name)
    
    def _polish_content(self, content: str, model_name: str = "deepseek_chat") -> str:
        """润色内容，提升语言质量"""
        messages = [
            {"role": "system", "content": "你是一位语言润色专家，擅长提升文本的语言质量。"}
        ]
        
        user_content = f"""
        请润色以下内容，提升语言质量：
        
        {content}
        
        润色要求：
        1. 保持内容原意不变
        2. 提升语言的流畅度和表现力
        3. 优化句子结构和词汇选择
        4. 保持原文风格
        """
        
        messages.append({"role": "user", "content": user_content})
        
        return LLMCaller.call(messages, model_name)

# 创建全局实例，方便其他模块调用
enhancer = NovelEnhancer()