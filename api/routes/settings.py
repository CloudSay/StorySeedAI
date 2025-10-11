"""
设定管理路由
"""

import os
import json
import re
from flask import request, jsonify
from . import settings_bp

@settings_bp.route('/settings/<novel_id>', methods=['GET'])
def get_settings_list(novel_id):
    """获取指定小说的设定文件列表"""
    try:
        data_path = "./data"
        if not os.path.exists(data_path):
            return jsonify({
                "character_versions": [],
                "world_versions": []
            })
        
        character_versions = []
        world_versions = []
        
        # 扫描data目录中的文件
        for filename in os.listdir(data_path):
            # 匹配人物设定文件: {novel_id}_chapter_{version}_state.json
            character_match = re.match(rf'{re.escape(novel_id)}_chapter_(\d+)_state\.json', filename)
            if character_match:
                version = int(character_match.group(1))
                character_versions.append({
                    "version": version,
                    "filename": filename
                })
            
            # 匹配世界设定文件: {novel_id}_world_bible_{version}.json
            world_match = re.match(rf'{re.escape(novel_id)}_world_bible_(\d+)\.json', filename)
            if world_match:
                version = int(world_match.group(1))
                world_versions.append({
                    "version": version,
                    "filename": filename
                })
        
        # 按版本号排序
        character_versions.sort(key=lambda x: x['version'])
        world_versions.sort(key=lambda x: x['version'])
        
        return jsonify({
            "character_versions": character_versions,
            "world_versions": world_versions
        })
        
    except Exception as e:
        print(f"获取设定列表失败: {e}")
        return jsonify({"error": f"获取设定列表失败: {str(e)}"}), 500

@settings_bp.route('/settings/<novel_id>/character/<version>', methods=['GET'])
def get_character_settings(novel_id, version):
    """获取指定版本的人物设定"""
    try:
        # 构建文件路径
        filename = f"{novel_id}_chapter_{version}_state.json"
        file_path = os.path.join("./data", filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "人物设定文件不存在"}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        return jsonify({
            "content": content,
            "filename": filename,
            "version": version
        })
        
    except Exception as e:
        print(f"获取人物设定失败: {e}")
        return jsonify({"error": f"获取人物设定失败: {str(e)}"}), 500

@settings_bp.route('/settings/<novel_id>/world/<version>', methods=['GET'])
def get_world_settings(novel_id, version):
    """获取指定版本的世界设定"""
    try:
        # 构建文件路径
        filename = f"{novel_id}_world_bible_{version}.json"
        file_path = os.path.join("./data", filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "世界设定文件不存在"}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        return jsonify({
            "content": content,
            "filename": filename,
            "version": version
        })
        
    except Exception as e:
        print(f"获取世界设定失败: {e}")
        return jsonify({"error": f"获取世界设定失败: {str(e)}"}), 500

@settings_bp.route('/settings/<novel_id>/character/<version>', methods=['PUT'])
def save_character_settings(novel_id, version):
    """保存人物设定"""
    try:
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({"error": "设定内容不能为空"}), 400
        
        # 确保data目录存在
        os.makedirs("./data", exist_ok=True)
        
        # 构建文件路径
        filename = f"{novel_id}_chapter_{version}_state.json"
        file_path = os.path.join("./data", filename)
        
        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            "success": True,
            "filename": filename,
            "version": version
        })
        
    except Exception as e:
        print(f"保存人物设定失败: {e}")
        return jsonify({"error": f"保存人物设定失败: {str(e)}"}), 500

@settings_bp.route('/settings/<novel_id>/world/<version>', methods=['PUT'])
def save_world_settings(novel_id, version):
    """保存世界设定"""
    try:
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({"error": "设定内容不能为空"}), 400
        
        # 确保data目录存在
        os.makedirs("./data", exist_ok=True)
        
        # 构建文件路径
        filename = f"{novel_id}_world_bible_{version}.json"
        file_path = os.path.join("./data", filename)
        
        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            "success": True,
            "filename": filename,
            "version": version
        })
        
    except Exception as e:
        print(f"保存世界设定失败: {e}")
        return jsonify({"error": f"保存世界设定失败: {str(e)}"}), 500

@settings_bp.route('/settings/<novel_id>/character/new', methods=['POST'])
def create_new_character_version(novel_id):
    """创建新的人物设定版本"""
    try:
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({"error": "设定内容不能为空"}), 400
        
        # 扫描现有版本，找到最大版本号
        data_path = "./data"
        max_version = -1
        
        if os.path.exists(data_path):
            for filename in os.listdir(data_path):
                match = re.match(rf'{re.escape(novel_id)}_chapter_(\d+)_state\.json', filename)
                if match:
                    version = int(match.group(1))
                    max_version = max(max_version, version)
        
        # 新版本号
        new_version = max_version + 1
        new_version_str = str(new_version).zfill(3)
        
        # 确保data目录存在
        os.makedirs(data_path, exist_ok=True)
        
        # 构建新文件路径
        filename = f"{novel_id}_chapter_{new_version_str}_state.json"
        file_path = os.path.join(data_path, filename)
        
        # 保存新版本
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            "success": True,
            "new_version": new_version_str,
            "filename": filename
        })
        
    except Exception as e:
        print(f"创建新人物设定版本失败: {e}")
        return jsonify({"error": f"创建新版本失败: {str(e)}"}), 500

@settings_bp.route('/settings/<novel_id>/world/new', methods=['POST'])
def create_new_world_version(novel_id):
    """创建新的世界设定版本"""
    try:
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({"error": "设定内容不能为空"}), 400
        
        # 扫描现有版本，找到最大版本号
        data_path = "./data"
        max_version = -1
        
        if os.path.exists(data_path):
            for filename in os.listdir(data_path):
                match = re.match(rf'{re.escape(novel_id)}_world_bible_(\d+)\.json', filename)
                if match:
                    version = int(match.group(1))
                    max_version = max(max_version, version)
        
        # 新版本号
        new_version = max_version + 1
        new_version_str = str(new_version).zfill(2)
        
        # 确保data目录存在
        os.makedirs(data_path, exist_ok=True)
        
        # 构建新文件路径
        filename = f"{novel_id}_world_bible_{new_version_str}.json"
        file_path = os.path.join(data_path, filename)
        
        # 保存新版本
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            "success": True,
            "new_version": new_version_str,
            "filename": filename
        })
        
    except Exception as e:
        print(f"创建新世界设定版本失败: {e}")
        return jsonify({"error": f"创建新版本失败: {str(e)}"}), 500