"""
模板管理路由
"""

import os
import json
import time
from flask import request, jsonify
from . import templates_bp
from .. import TEMPLATES_DIR

def load_template_index():
    """加载模版索引文件"""
    index_file = os.path.join(TEMPLATES_DIR, "template_index.json")
    if os.path.exists(index_file):
        with open(index_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"version": "1.0", "templates": {}}

def save_template_index(index_data):
    """保存模版索引文件"""
    index_file = os.path.join(TEMPLATES_DIR, "template_index.json")
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

@templates_bp.route('/templates', methods=['GET'])
def get_templates():
    """获取模版列表"""
    try:
        index_data = load_template_index()
        return jsonify(index_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@templates_bp.route('/templates', methods=['POST'])
def save_template():
    """保存模版"""
    try:
        data = request.json
        
        # 验证必需字段
        required_fields = ['id', 'name', 'files', 'contents']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"缺少必需字段: {field}"}), 400
        
        template_id = data['id']
        
        # 加载现有索引
        index_data = load_template_index()
        
        # 保存提示词文件
        for file_type, content in data['contents'].items():
            filename = data['files'][file_type]
            file_path = os.path.join(TEMPLATES_DIR, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 更新索引
        template_info = {
            "id": template_id,
            "name": data['name'],
            "category": data.get('category', ''),
            "description": data.get('description', ''),
            "author": "用户创建",
            "created_date": time.strftime("%Y-%m-%d"),
            "files": data['files'],
            "word_count_range": data.get('word_count_range', {"min": 2000, "max": 3000})
        }
        
        index_data['templates'][template_id] = template_info
        index_data['last_updated'] = time.strftime("%Y-%m-%d")
        
        # 保存索引
        save_template_index(index_data)
        
        return jsonify({"message": "模版保存成功", "template_id": template_id})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@templates_bp.route('/template-file/<filename>')
def get_template_file(filename):
    """获取模版文件内容"""
    try:
        file_path = os.path.join(TEMPLATES_DIR, filename)
        if not os.path.exists(file_path):
            # 如果模版文件不存在，尝试从prompts目录读取默认文件
            prompts_path = os.path.join("./prompts", filename.split('_', 1)[-1])
            if os.path.exists(prompts_path):
                with open(prompts_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return "", 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500