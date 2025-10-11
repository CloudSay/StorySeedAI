"""
增强功能路由
"""

from flask import request, jsonify
from . import enhance_bp
from modules.enhanced_features import NovelEnhancer, ContentModerator, DialogueOptimizer, StyleTransfer, PlotPlanner
from modules.data_models import ChapterState

# 全局实例
enhancer = NovelEnhancer()

@enhance_bp.route('/enhance/chapter', methods=['POST'])
def enhance_chapter():
    """增强章节内容"""
    try:
        data = request.json
        content = data.get('content', '')
        options = data.get('options', {})
        model_name = data.get('model_name', 'deepseek_chat')
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        result = enhancer.enhance_chapter(content, options, model_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhance_bp.route('/generate/outline', methods=['POST'])
def generate_chapter_outline():
    """生成章节大纲"""
    try:
        data = request.json
        novel_id = data.get('novel_id', '')
        current_chapter = data.get('current_chapter', 0)
        world_bible = data.get('world_bible', {})
        current_state_data = data.get('current_state', {})
        previous_content = data.get('previous_content', '')
        model_name = data.get('model_name', 'deepseek_chat')
        
        if not novel_id:
            return jsonify({'error': 'Novel ID is required'}), 400
        
        # 重建ChapterState对象
        current_state = None
        if current_state_data:
            try:
                current_state = ChapterState(**current_state_data)
            except:
                pass
        
        outline = PlotPlanner.generate_chapter_outline(
            novel_id, current_chapter, world_bible, current_state, previous_content, model_name
        )
        
        return jsonify({'outline': outline})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhance_bp.route('/generate/story-arc', methods=['POST'])
def generate_story_arc():
    """生成故事弧线规划"""
    try:
        data = request.json
        novel_id = data.get('novel_id', '')
        world_bible = data.get('world_bible', {})
        protagonist_profile = data.get('protagonist_profile', {})
        model_name = data.get('model_name', 'deepseek_chat')
        
        if not novel_id:
            return jsonify({'error': 'Novel ID is required'}), 400
        
        story_arc = PlotPlanner.generate_story_arc(
            novel_id, world_bible, protagonist_profile, model_name
        )
        
        return jsonify(story_arc)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhance_bp.route('/moderate/content', methods=['POST'])
def moderate_content():
    """审查内容"""
    try:
        data = request.json
        content = data.get('content', '')
        model_name = data.get('model_name', 'deepseek_chat')
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        result = ContentModerator.moderate_content(content, model_name)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhance_bp.route('/optimize/dialogue', methods=['POST'])
def optimize_dialogue():
    """优化对话内容"""
    try:
        data = request.json
        dialogue = data.get('dialogue', '')
        character_profiles = data.get('character_profiles', {})
        model_name = data.get('model_name', 'deepseek_chat')
        
        if not dialogue:
            return jsonify({'error': 'Dialogue is required'}), 400
        
        if not character_profiles:
            return jsonify({'error': 'Character profiles are required'}), 400
        
        result = DialogueOptimizer.optimize_dialogue(dialogue, character_profiles, model_name)
        
        return jsonify({'optimized_dialogue': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhance_bp.route('/transfer/style', methods=['POST'])
def transfer_style():
    """风格迁移"""
    try:
        data = request.json
        content = data.get('content', '')
        style_prompt = data.get('style_prompt', '')
        model_name = data.get('model_name', 'deepseek_chat')
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        if not style_prompt:
            return jsonify({'error': 'Style prompt is required'}), 400
        
        result = StyleTransfer.transfer_style(content, style_prompt, model_name)
        
        return jsonify({'styled_content': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500