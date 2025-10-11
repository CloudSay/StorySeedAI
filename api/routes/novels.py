"""
小说生成和管理路由
"""

import os
import json
import time
import glob
import re
from flask import request, jsonify
from . import novels_bp
from .. import TEMPLATES_DIR, XIAOSHUO_DIR
from main import NovelGenerator

# 全局实例
generator = NovelGenerator()

def load_template_index():
    """加载模版索引文件"""
    index_file = os.path.join(TEMPLATES_DIR, "template_index.json")
    if os.path.exists(index_file):
        with open(index_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"version": "1.0", "templates": {}}

@novels_bp.route('/generate', methods=['POST'])
def generate_novel():
    """生成小说"""
    try:
        data = request.json
        
        # 获取参数
        template_id = data.get("template_id")
        chapter_outline = data.get("chapter_outline")  # 改为章节细纲
        model_name = data.get("model_name", "deepseek_chat")
        update_model_name = data.get("update_model_name")
        use_state = data.get("use_state", True)
        use_world_bible = data.get("use_world_bible", True)
        update_state = data.get("update_state", False)
        session_id = data.get("session_id", "default")
        novel_id = data.get("novel_id")
        use_previous_chapters = data.get("use_previous_chapters", False)
        previous_chapters_count = data.get("previous_chapters_count", 1)
        
        if not template_id:
            return jsonify({"error": "缺少模版ID"}), 400
        
        if not chapter_outline:
            return jsonify({"error": "缺少章节细纲"}), 400
        
        # 加载模版
        index_data = load_template_index()
        if template_id not in index_data['templates']:
            return jsonify({"error": f"模版不存在: {template_id}"}), 404
        
        template = index_data['templates'][template_id]
        
        # 读取模版文件内容
        writer_role_file = os.path.join(TEMPLATES_DIR, template['files']['writer_role'])
        writing_rules_file = os.path.join(TEMPLATES_DIR, template['files']['writing_rules'])
        
        writer_role = ""
        writing_rules = ""
        
        if os.path.exists(writer_role_file):
            with open(writer_role_file, 'r', encoding='utf-8') as f:
                writer_role = f.read()
        
        if os.path.exists(writing_rules_file):
            with open(writing_rules_file, 'r', encoding='utf-8') as f:
                writing_rules = f.read()
        
        # 构建系统提示
        system_prompt = f"{writer_role}\n\n{writing_rules}".strip()
        
        # 生成内容
        content = generator.generate_chapter(
            chapter_outline=chapter_outline,  # 使用章节细纲
            model_name=model_name,
            system_prompt=system_prompt,
            session_id=session_id,
            use_state=use_state,
            use_world_bible=use_world_bible,
            update_state=update_state,
            update_model_name=update_model_name,
            novel_id=novel_id,
            use_previous_chapters=use_previous_chapters,
            previous_chapters_count=previous_chapters_count
        )
        
        return jsonify({
            "content": content,
            "template_used": template.get('name', template_id),
            "novel_id": novel_id,
            "word_count": len(content),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        print(f"生成错误: {e}")
        return jsonify({"error": str(e)}), 500

@novels_bp.route('/novels', methods=['GET'])
def get_novels():
    """获取所有小说列表"""
    try:
        novels = generator.state_manager.list_novels()
        return jsonify({"novels": novels})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@novels_bp.route('/novels/<novel_id>/states', methods=['GET'])
def get_novel_states(novel_id):
    """获取指定小说的状态文件列表"""
    try:
        states = generator.state_manager.list_novel_states(novel_id)
        # 提取文件信息
        state_info = []
        for state_file in states:
            filename = os.path.basename(state_file)
            # 提取章节编号
            parts = filename.split('_')
            if len(parts) >= 3:
                chapter_index = int(parts[2])
                state_info.append({
                    "file": filename,
                    "chapter_index": chapter_index,
                    "path": state_file
                })
        
        # 按章节编号排序
        state_info.sort(key=lambda x: x["chapter_index"])
        
        return jsonify({
            "novel_id": novel_id,
            "states": state_info
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@novels_bp.route('/novels/<novel_id>/latest-state', methods=['GET'])
def get_latest_state(novel_id):
    """获取指定小说的最新状态"""
    try:
        state = generator.state_manager.load_latest_state(novel_id)
        if state:
            return jsonify({
                "novel_id": novel_id,
                "state": state.model_dump(),
                "found": True
            })
        else:
            return jsonify({
                "novel_id": novel_id,
                "state": None,
                "found": False
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@novels_bp.route('/save-result', methods=['POST'])
def save_result():
    """保存生成结果"""
    try:
        data = request.json
        
        if 'content' not in data:
            return jsonify({"error": "缺少内容"}), 400
        
        content = data['content']
        novel_id = data.get('novel_id')  # 获取小说ID
        
        # 生成文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        if novel_id:
            filename = f"{novel_id}_novel_{timestamp}.txt"
        else:
            filename = f"novel_{timestamp}.txt"
        
        file_path = os.path.join(XIAOSHUO_DIR, filename)
        
        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            "message": "保存成功",
            "filename": filename,
            "file_path": file_path,
            "novel_id": novel_id,
            "word_count": len(content)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@novels_bp.route('/novels/<novel_id>/info', methods=['GET'])
def get_novel_info(novel_id):
    """获取指定小说的完整信息"""
    try:
        # 1. 获取状态信息
        state = generator.state_manager.load_latest_state(novel_id)
        state_info = {
            "found": state is not None,
            "latest_chapter": state.chapter_index if state else 0,
            "protagonist": state.protagonist.name if state else "未知",
            "level": state.protagonist.level if state else "未知",
            "plot_summary": state.current_plot_summary if state else ""
        }
        
        # 2. 检查章节文件
        chapter_files = glob.glob(os.path.join(XIAOSHUO_DIR, f"{novel_id}_chapter_*.txt"))
        chapter_numbers = []
        for file_path in chapter_files:
            filename = os.path.basename(file_path)
            # 提取章节编号: novel_id_chapter_XXX.txt
            match = re.search(r'_chapter_(\d+)\.txt$', filename)
            if match:
                chapter_numbers.append(int(match.group(1)))
        
        chapter_numbers.sort()
        chapter_info = {
            "total_chapters": len(chapter_numbers),
            "chapter_list": chapter_numbers,
            "latest_chapter_file": max(chapter_numbers) if chapter_numbers else 0
        }
        
        # 3. 获取记忆统计
        try:
            memory_stats = generator.get_memory_stats(novel_id)
            memory_info = {
                "total_messages": memory_stats.get("total_messages", 0),
                "total_chunks": memory_stats.get("total_chunks", 0),
                "compressed_chunks": memory_stats.get("compressed_chunks", 0)
            }
        except:
            memory_info = {
                "total_messages": 0,
                "total_chunks": 0,
                "compressed_chunks": 0
            }
        
        # 4. 检查世界设定文件
        world_bible = generator.state_manager.load_world_bible(novel_id)
        world_info = {
            "has_world_bible": bool(world_bible),
            "world_setting": world_bible.get("setting", "") if world_bible else ""
        }
        
        # 5. 检查版本文件
        version_files = glob.glob(os.path.join("./versions", f"{novel_id}_chapter_*_versions.json"))
        version_info = {
            "has_versions": len(version_files) > 0,
            "version_chapters": len(version_files)
        }
        
        return jsonify({
            "novel_id": novel_id,
            "state": state_info,
            "chapters": chapter_info,
            "memory": memory_info,
            "world": world_info,
            "versions": version_info,
            "summary": {
                "state_chapter": state_info["latest_chapter"],
                "file_chapter": chapter_info["latest_chapter_file"],
                "sync_status": "同步" if state_info["latest_chapter"] == chapter_info["latest_chapter_file"] else "不同步"
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@novels_bp.route('/read-outline', methods=['POST'])
def read_outline():
    """读取章节细纲"""
    try:
        data = request.json
        novel_id = data.get('novel_id')
        chapter_index = data.get('chapter_index')
        
        if not novel_id or not chapter_index:
            return jsonify({"error": "缺少必需参数"}), 400
        
        # 构建细纲文件路径
        outline_dir = os.path.join("xiaoshuo", "zhangjiexigang", str(novel_id))
        outline_file = os.path.join(outline_dir, f"{chapter_index}.txt")
        
        # 检查文件是否存在
        if not os.path.exists(outline_file):
            return jsonify({
                "error": f"细纲文件不存在: {outline_file}",
                "outline": None
            }), 404
        
        # 读取细纲文件
        with open(outline_file, 'r', encoding='utf-8') as f:
            outline_content = f.read().strip()
        
        if not outline_content:
            return jsonify({
                "error": "细纲文件为空",
                "outline": None
            }), 400
        
        return jsonify({
            "outline": outline_content,
            "file_path": outline_file,
            "chapter_index": chapter_index,
            "novel_id": novel_id
        })
        
    except Exception as e:
        print(f"读取细纲失败: {e}")
        return jsonify({"error": str(e)}), 500

@novels_bp.route('/save-chapter', methods=['POST'])
def save_chapter():
    """保存章节到文件"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        novel_id = data.get('novel_id', '')
        chapter_index = data.get('chapter_index', 1)
        auto_save = data.get('auto_save', False)
        
        if not content:
            return jsonify({"error": "章节内容不能为空"}), 400
        
        # 确保xiaoshuo目录存在
        os.makedirs("./xiaoshuo", exist_ok=True)
        
        # 生成文件名
        if novel_id:
            filename = f"{novel_id}_chapter_{chapter_index:03d}.txt"
        else:
            filename = f"chapter_{chapter_index:03d}.txt"
        
        file_path = f"./xiaoshuo/{filename}"
        
        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            "success": True,
            "filename": filename,
            "file_path": file_path,
            "word_count": len(content),
            "auto_save": auto_save
        })
        
    except Exception as e:
        print(f"保存章节失败: {e}")
        return jsonify({"error": f"保存章节失败: {str(e)}"}), 500

@novels_bp.route('/update-state', methods=['POST'])
def update_state():
    """手动更新角色设定"""
    try:
        data = request.get_json()
        novel_id = data.get('novel_id')
        chapter_index = data.get('chapter_index')
        model_name = data.get('model_name')
        force_update = data.get('force_update', False)
        
        if not novel_id:
            return jsonify({"error": "缺少小说ID"}), 400
        
        if not chapter_index:
            return jsonify({"error": "缺少章节编号"}), 400
        
        # 读取章节内容
        chapter_filename = f"{novel_id}_chapter_{chapter_index:03d}.txt"
        chapter_path = os.path.join("./xiaoshuo", chapter_filename)
        
        if not os.path.exists(chapter_path):
            return jsonify({"error": f"章节文件不存在: {chapter_filename}"}), 404
        
        with open(chapter_path, 'r', encoding='utf-8') as f:
            chapter_content = f.read()
        
        # 加载当前状态
        current_state = generator.state_manager.load_latest_state(novel_id)
        if not current_state:
            return jsonify({"error": "找不到当前角色状态"}), 404
        
        # 使用生成器直接更新状态
        updated_state = generator.update_state(
            chapter_content=chapter_content,
            current_state=current_state,
            model_name=model_name or generator.model_name,
            novel_id=novel_id
        )
        
        return jsonify({
            "success": True,
            "novel_id": novel_id,
            "chapter_index": chapter_index,
            "summary": f"基于第{chapter_index}章内容更新了角色设定",
            "updated_fields": ["protagonist", "characters", "current_plot_summary"],
            "model_used": model_name or generator.model_name
        })
        
    except Exception as e:
        print(f"手动更新状态失败: {e}")
        return jsonify({"error": f"状态更新失败: {str(e)}"}), 500