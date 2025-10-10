// 全局状态管理
const AppState = {
    templates: {},
    currentTemplate: null,
    isGenerating: false
};

// API配置
const API_BASE = '/api';

// 工具函数
const Utils = {
    // 显示状态消息
    showStatus(elementId, message, type = 'info') {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = type === 'loading' ?
                `<span class="loading"></span>${message}` : message;
            element.className = `status ${type}`;
        }
    },

    // 显示错误消息
    showError(message) {
        alert(`错误: ${message}`);
        console.error(message);
    },

    // 格式化JSON
    formatJSON(obj) {
        return JSON.stringify(obj, null, 2);
    },

    // 解析JSON
    parseJSON(str) {
        try {
            return JSON.parse(str);
        } catch (e) {
            throw new Error(`JSON格式错误: ${e.message}`);
        }
    },

    // 复制到剪贴板
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            alert('已复制到剪贴板');
        } catch (err) {
            console.error('复制失败:', err);
            alert('复制失败，请手动复制');
        }
    }
};

// 标签页管理
class TabManager {
    constructor() {
        this.initTabs();
    }

    initTabs() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.dataset.tab;

                // 更新按钮状态
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // 更新内容显示
                tabContents.forEach(content => {
                    content.classList.remove('active');
                    if (content.id === targetTab) {
                        content.classList.add('active');
                    }
                });

                // 标签页切换时的特殊处理
                if (targetTab === 'template') {
                    TemplateManager.loadTemplates();
                } else if (targetTab === 'generate') {
                    NovelGenerator.loadTemplatesForGeneration();
                }
            });
        });
    }
}

// 模版管理器
class TemplateManager {
    constructor() {
        this.initEvents();
        this.loadTemplates();
    }

    initEvents() {
        // 模版选择
        document.getElementById('templateSelect').addEventListener('change', (e) => {
            this.selectTemplate(e.target.value);
        });

        // 新建模版
        document.getElementById('newTemplateBtn').addEventListener('click', () => {
            this.newTemplate();
        });

        // 保存模版
        document.getElementById('saveTemplateBtn').addEventListener('click', () => {
            this.saveTemplate();
        });

        // 预览模版
        document.getElementById('previewTemplateBtn').addEventListener('click', () => {
            this.previewTemplate();
        });
    }

    async loadTemplates() {
        try {
            const response = await fetch(`${API_BASE}/templates`);
            if (!response.ok) throw new Error('加载模版失败');

            const data = await response.json();
            AppState.templates = data.templates || {};

            this.updateTemplateSelect();
        } catch (error) {
            Utils.showError(`加载模版失败: ${error.message}`);
        }
    }

    updateTemplateSelect() {
        const select = document.getElementById('templateSelect');

        // 检查元素是否存在
        if (!select) {
            console.error('templateSelect元素不存在');
            return;
        }

        // 清空选项
        select.innerHTML = '<option value="">选择模版...</option>';

        // 添加模版选项
        Object.values(AppState.templates).forEach(template => {
            const option = new Option(`${template.name} (${template.id})`, template.id);
            select.appendChild(option);
        });
    }

    selectTemplate(templateId) {
        if (!templateId) {
            this.clearEditor();
            return;
        }

        const template = AppState.templates[templateId];
        if (!template) return;

        AppState.currentTemplate = template;
        this.loadTemplateToEditor(template);
        this.showTemplateInfo(template);
    }

    async loadTemplateToEditor(template) {
        try {
            // 加载三个提示词文件内容
            const [writerRole, writingRules, updateStateRules] = await Promise.all([
                this.loadTemplateFile(template.files.writer_role),
                this.loadTemplateFile(template.files.writing_rules),
                this.loadTemplateFile(template.files.update_state_rules)
            ]);

            // 填充编辑器
            document.getElementById('templateId').value = template.id;
            document.getElementById('templateName').value = template.name;
            document.getElementById('templateCategory').value = template.category || '';
            document.getElementById('minWords').value = template.word_count_range?.min || '';
            document.getElementById('maxWords').value = template.word_count_range?.max || '';
            document.getElementById('writerRole').value = writerRole;
            document.getElementById('writingRules').value = writingRules;
            document.getElementById('updateStateRules').value = updateStateRules;

        } catch (error) {
            Utils.showError(`加载模版内容失败: ${error.message}`);
        }
    }

    async loadTemplateFile(filename) {
        try {
            const response = await fetch(`${API_BASE}/template-file/${filename}`);
            if (!response.ok) throw new Error(`加载文件失败: ${filename}`);
            return await response.text();
        } catch (error) {
            console.warn(`加载文件失败: ${filename}`, error);
            return '';
        }
    }

    showTemplateInfo(template) {
        const infoDiv = document.getElementById('templateInfo');
        if (!infoDiv) {
            console.error('templateInfo元素不存在');
            return;
        }

        infoDiv.innerHTML = `
            <h4>${template.name}</h4>
            <p><strong>ID:</strong> ${template.id}</p>
            <p><strong>分类:</strong> ${template.category || '未分类'}</p>
            <p><strong>字数范围:</strong> ${template.word_count_range?.min || 0} - ${template.word_count_range?.max || 0}</p>
            <p><strong>创建时间:</strong> ${template.created_date || '未知'}</p>
        `;
    }

    newTemplate() {
        this.clearEditor();
        // 生成新的模版ID
        const existingIds = Object.keys(AppState.templates).map(id => parseInt(id)).filter(id => !isNaN(id));
        const newId = existingIds.length > 0 ? Math.max(...existingIds) + 1 : 1;
        document.getElementById('templateId').value = String(newId).padStart(3, '0');
    }

    clearEditor() {
        document.getElementById('templateId').value = '';
        document.getElementById('templateName').value = '';
        document.getElementById('templateCategory').value = '';
        document.getElementById('minWords').value = '';
        document.getElementById('maxWords').value = '';
        document.getElementById('writerRole').value = '';
        document.getElementById('writingRules').value = '';
        document.getElementById('updateStateRules').value = '';
        const templateInfo = document.getElementById('templateInfo');
        if (templateInfo) {
            templateInfo.innerHTML = '';
        }
        AppState.currentTemplate = null;
    }

    async saveTemplate() {
        try {
            const templateData = this.collectTemplateData();

            const response = await fetch(`${API_BASE}/templates`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(templateData)
            });

            if (!response.ok) throw new Error('保存模版失败');

            alert('模版保存成功！');
            await this.loadTemplates();

        } catch (error) {
            Utils.showError(`保存模版失败: ${error.message}`);
        }
    }

    collectTemplateData() {
        const id = document.getElementById('templateId').value.trim();
        const name = document.getElementById('templateName').value.trim();

        if (!id || !name) {
            throw new Error('请填写模版ID和名称');
        }

        return {
            id,
            name,
            category: document.getElementById('templateCategory').value.trim(),
            word_count_range: {
                min: parseInt(document.getElementById('minWords').value) || 2000,
                max: parseInt(document.getElementById('maxWords').value) || 3000
            },
            files: {
                writer_role: `${id}_writer_role.txt`,
                writing_rules: `${id}_writing_rules.txt`,
                update_state_rules: `${id}_update_state_rules.txt`
            },
            contents: {
                writer_role: document.getElementById('writerRole').value.trim(),
                writing_rules: document.getElementById('writingRules').value.trim(),
                update_state_rules: document.getElementById('updateStateRules').value.trim()
            }
        };
    }

    previewTemplate() {
        try {
            const templateData = this.collectTemplateData();
            const preview = `
=== 模版预览 ===
ID: ${templateData.id}
名称: ${templateData.name}
分类: ${templateData.category}
字数范围: ${templateData.word_count_range.min} - ${templateData.word_count_range.max}

=== 角色定义 ===
${templateData.contents.writer_role}

=== 写作规则 ===
${templateData.contents.writing_rules}

=== 状态更新规则 ===
${templateData.contents.update_state_rules}
            `;

            const previewWindow = window.open('', '_blank', 'width=800,height=600');
            previewWindow.document.write(`
                <html>
                <head><title>模版预览</title></head>
                <body style="font-family: monospace; padding: 20px; white-space: pre-wrap;">
                ${preview.replace(/\n/g, '<br>')}
                </body>
                </html>
            `);
        } catch (error) {
            Utils.showError(`预览失败: ${error.message}`);
        }
    }
}

// 批量生成管理器
class BatchGenerator {
    constructor() {
        this.isRunning = false;
        this.shouldStop = false;
        this.currentChapter = 0;
        this.totalChapters = 0;
        this.initEvents();
        this.loadTemplatesForBatch();
    }

    initEvents() {
        // 检测进度按钮
        document.getElementById('loadBatchNovelBtn').addEventListener('click', () => {
            this.detectProgress();
        });

        // 开始批量生成
        document.getElementById('startBatchBtn').addEventListener('click', () => {
            this.startBatchGeneration();
        });

        // 停止批量生成
        document.getElementById('stopBatchBtn').addEventListener('click', () => {
            this.stopBatchGeneration();
        });

        // 手动更新角色设定
        document.getElementById('manualUpdateStateBtn').addEventListener('click', () => {
            this.manualUpdateState();
        });
    }

    async loadTemplatesForBatch() {
        try {
            const response = await fetch(`${API_BASE}/templates`);
            if (!response.ok) throw new Error('获取模版失败');

            const data = await response.json();
            const select = document.getElementById('batchTemplateSelect');

            // 检查元素是否存在
            if (!select) {
                throw new Error('batchTemplateSelect元素不存在');
            }

            // 清空现有选项
            select.innerHTML = '<option value="">选择模版...</option>';

            // 添加模版选项
            Object.entries(data.templates).forEach(([id, template]) => {
                const option = document.createElement('option');
                option.value = id;
                option.textContent = `${template.name} (${id})`;
                select.appendChild(option);
            });
        } catch (error) {
            this.addLog(`模版加载失败: ${error.message}`, 'error');
        }
    }

    async detectProgress() {
        const novelId = document.getElementById('batchNovelId').value.trim();
        if (!novelId) {
            alert('请输入小说ID');
            return;
        }

        try {
            // 获取小说信息
            const response = await fetch(`${API_BASE}/novels/${novelId}/info`);
            if (!response.ok) throw new Error('获取小说信息失败');

            const info = await response.json();

            // 显示当前进度
            const maxChapter = info.chapters.latest_chapter_file || 0;
            const nextChapter = maxChapter + 1;

            let infoText = `📊 当前进度：已生成 ${maxChapter} 章\n`;
            infoText += `➡️ 下一章：第 ${nextChapter} 章\n`;
            infoText += `📁 章节文件：${info.chapters.total_chapters} 个\n`;
            infoText += `💾 状态同步：${info.summary.sync_status}\n`;
            infoText += `🧠 记忆分片：${info.memory.total_chunks} 个`;

            this.showBatchInfo(infoText, 'success');
            this.addLog(`检测到小说 ${novelId}，当前已生成 ${maxChapter} 章，下一章为第 ${nextChapter} 章`, 'info');

        } catch (error) {
            this.showBatchInfo(`检测失败: ${error.message}`, 'error');
            this.addLog(`进度检测失败: ${error.message}`, 'error');
        }
    }

    extractMaxChapter(info) {
        // 使用新的API数据结构
        return info.chapters ? info.chapters.latest_chapter_file || 0 : 0;
    }

    async startBatchGeneration() {
        // 强化防重复执行检查
        if (this.isRunning) {
            this.addLog('生成已在进行中，请耐心等待...', 'warning');
            return;
        }

        // 立即禁用按钮防止重复点击
        const startBtn = document.getElementById('startBatchBtn');
        const stopBtn = document.getElementById('stopBatchBtn');

        if (startBtn.disabled) {
            this.addLog('请等待当前操作完成...', 'warning');
            return;
        }

        // 验证输入
        const novelId = document.getElementById('batchNovelId').value.trim();
        const templateId = document.getElementById('batchTemplateSelect').value;
        const chapterCount = parseInt(document.getElementById('batchChapterCount').value);

        if (!novelId) {
            alert('请输入小说ID');
            return;
        }

        if (!templateId) {
            alert('请选择模版');
            return;
        }

        if (!chapterCount || chapterCount < 1) {
            alert('请输入有效的章节数量');
            return;
        }

        try {
            // 显示初始化状态
            this.showLoadingState('正在初始化...', 'info');

            // 检测当前进度
            const response = await fetch(`${API_BASE}/novels/${novelId}/info`);
            if (!response.ok) throw new Error('获取小说信息失败');

            const info = await response.json();
            const currentMaxChapter = this.extractMaxChapter(info);
            const startChapter = currentMaxChapter + 1;

            // 初始化批量生成状态
            this.isRunning = true;
            this.shouldStop = false;
            this.currentChapter = 0;
            this.totalChapters = chapterCount;

            // 更新UI - 立即禁用开始按钮，启用停止按钮
            startBtn.disabled = true;
            stopBtn.disabled = false;

            this.showLoadingState('正在生成中，请耐心等待约3分钟...', 'info');
            this.updateProgress(0, chapterCount);
            this.addLog(`开始批量生成，从第 ${startChapter} 章开始，共生成 ${chapterCount} 章`, 'info');
            this.addLog(`💡 提示：生成过程需要约3分钟，请耐心等待，系统正在努力工作中...`, 'info');

            // 执行批量生成
            for (let i = 0; i < chapterCount; i++) {
                if (this.shouldStop) {
                    this.addLog('用户手动停止生成', 'warning');
                    this.showLoadingState('生成已停止', 'warning');
                    break;
                }

                const chapterIndex = startChapter + i;
                this.currentChapter = i + 1;

                try {
                    await this.generateSingleChapter(novelId, templateId, chapterIndex);
                    this.updateProgress(this.currentChapter, this.totalChapters);
                    this.showLoadingState(`已完成 ${this.currentChapter}/${this.totalChapters} 章，${chapterCount - this.currentChapter > 0 ? '继续生成中...' : '即将完成...'}`, 'info');
                } catch (error) {
                    this.addLog(`第 ${chapterIndex} 章生成失败: ${error.message}`, 'error');
                    this.showLoadingState(`第 ${chapterIndex} 章生成失败，生成已停止`, 'error');
                    break;
                }
            }

            // 完成
            this.addLog('批量生成完成！', 'success');
            this.showLoadingState('🎉 所有章节生成完成！', 'success');
            // 3秒后自动隐藏状态
            setTimeout(() => {
                this.hideLoadingState();
            }, 3000);

        } catch (error) {
            this.addLog(`批量生成启动失败: ${error.message}`, 'error');
            this.hideLoadingState();
        } finally {
            // 恢复按钮状态
            this.isRunning = false;
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
    }

    async generateSingleChapter(novelId, templateId, chapterIndex) {
        this.addLog(`正在生成第 ${chapterIndex} 章...`, 'info');
        this.showLoadingState(`正在生成第 ${chapterIndex} 章，请耐心等待...`, 'info');

        // 1. 读取章节细纲
        const outline = await this.loadChapterOutline(novelId, chapterIndex);
        if (!outline) {
            throw new Error(`找不到第 ${chapterIndex} 章的细纲文件`);
        }

        // 2. 收集生成参数
        const updateModelSelect = document.getElementById('batchUpdateModelSelect');
        const updateModelName = updateModelSelect.value || null;

        const generateData = {
            template_id: templateId,
            chapter_outline: outline,
            model_name: document.getElementById('batchModelSelect').value,
            update_model_name: updateModelName,
            use_state: document.getElementById('batchUseState').checked,
            use_world_bible: document.getElementById('batchUseWorldBible').checked,
            update_state: document.getElementById('batchUpdateState').checked,
            session_id: novelId,
            novel_id: novelId,
            use_previous_chapters: document.getElementById('batchUsePreviousChapters').checked,
            previous_chapters_count: parseInt(document.getElementById('batchPreviousChaptersCount').value) || 1
        };

        // 3. 调用生成API
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(generateData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '生成失败');
        }

        const result = await response.json();

        // 4. 自动保存到正确的文件路径
        await this.autoSaveChapter(result.content, novelId, chapterIndex);

        this.addLog(`第 ${chapterIndex} 章生成成功 (${result.word_count} 字)，已自动保存`, 'success');
        this.showLoadingState(`第 ${chapterIndex} 章生成完成，继续生成下一章...`, 'info');
    }

    async autoSaveChapter(content, novelId, chapterIndex) {
        try {
            // 调用后端保存API，使用正确的文件命名格式
            const saveData = {
                content: content,
                novel_id: novelId,
                chapter_index: chapterIndex,
                auto_save: true  // 标识这是自动保存
            };

            const response = await fetch(`${API_BASE}/save-chapter`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(saveData)
            });

            if (!response.ok) {
                throw new Error('自动保存失败');
            }

            const result = await response.json();
            this.addLog(`章节已保存为: ${result.filename}`, 'info');

        } catch (error) {
            this.addLog(`自动保存失败: ${error.message}`, 'warning');
        }
    }

    async loadChapterOutline(novelId, chapterIndex) {
        try {
            // 构建细纲文件路径
            const outlinePath = `xiaoshuo/zhangjiexigang/${novelId}/${chapterIndex}.txt`;

            // 这里需要后端提供读取细纲文件的API
            // 暂时返回一个默认细纲，实际应该从文件读取
            const response = await fetch(`${API_BASE}/read-outline`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    novel_id: novelId,
                    chapter_index: chapterIndex
                })
            });

            if (response.ok) {
                const data = await response.json();
                return data.outline;
            } else {
                // 如果API不存在，返回默认细纲
                return `【第${chapterIndex}章】\n\n开场：\n- 继续上一章的剧情发展\n\n发展：\n- 推进主线剧情\n\n高潮：\n- 制造冲突和转折\n\n结尾：\n- 为下一章留下悬念\n\n目标字数：2800字`;
            }

        } catch (error) {
            this.addLog(`读取第 ${chapterIndex} 章细纲失败: ${error.message}`, 'warning');
            // 返回默认细纲
            return `【第${chapterIndex}章】\n\n开场：\n- 继续上一章的剧情发展\n\n发展：\n- 推进主线剧情\n\n高潮：\n- 制造冲突和转折\n\n结尾：\n- 为下一章留下悬念\n\n目标字数：2800字`;
        }
    }

    stopBatchGeneration() {
        if (this.isRunning) {
            this.shouldStop = true;
            this.addLog('正在停止批量生成...', 'warning');
            this.hideLoadingState();
        }
    }

    updateProgress(current, total) {
        const percentage = total > 0 ? (current / total) * 100 : 0;
        document.getElementById('progressFill').style.width = `${percentage}%`;
        document.getElementById('progressText').textContent = `进度: ${current}/${total} (${percentage.toFixed(1)}%)`;
    }

    addLog(message, type = 'info') {
        const logContainer = document.getElementById('batchLog');
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;

        const timestamp = new Date().toLocaleTimeString();
        logEntry.textContent = `[${timestamp}] ${message}`;

        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    showBatchInfo(message, type = 'info') {
        const infoDiv = document.getElementById('batchNovelInfo');
        infoDiv.className = `novel-info ${type}`;
        infoDiv.textContent = message;
    }

    showLoadingState(message, type = 'info') {
        const statusDiv = document.getElementById('batchStatus');
        statusDiv.innerHTML = `<span class="loading"></span>${message}`;
        statusDiv.className = `status ${type}`;
    }

    hideLoadingState() {
        const statusDiv = document.getElementById('batchStatus');
        statusDiv.innerHTML = '';
        statusDiv.className = 'status';
    }

    async manualUpdateState() {
        const novelId = document.getElementById('batchNovelId').value.trim();
        if (!novelId) {
            alert('请输入小说ID');
            return;
        }

        // 检查是否有最新章节内容可用于更新
        try {
            this.showLoadingState('正在手动更新角色设定...', 'info');
            this.addLog('开始手动更新角色设定...', 'info');

            // 获取小说信息，找到最新章节
            const infoResponse = await fetch(`${API_BASE}/novels/${novelId}/info`);
            if (!infoResponse.ok) throw new Error('获取小说信息失败');

            const info = await infoResponse.json();
            const latestChapter = this.extractMaxChapter(info);

            if (latestChapter === 0) {
                throw new Error('没有找到可用的章节内容进行状态更新');
            }

            // 读取最新章节内容
            const chapterPath = `xiaoshuo/${novelId}_chapter_${latestChapter.toString().padStart(3, '0')}.txt`;

            // 构建更新请求数据
            const updateModelSelect = document.getElementById('batchUpdateModelSelect');

            const updateModelName = updateModelSelect.value || document.getElementById('batchModelSelect').value;

            const updateData = {
                novel_id: novelId,
                chapter_index: latestChapter,
                model_name: updateModelName,
                force_update: true  // 标识这是手动更新
            };

            // 调用状态更新API
            const response = await fetch(`${API_BASE}/update-state`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updateData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || '状态更新失败');
            }

            const result = await response.json();
            this.addLog(`✅ 角色设定更新成功！基于第${latestChapter}章内容`, 'success');
            this.addLog(`📊 更新内容：${result.summary || '状态已同步'}`, 'info');
            this.hideLoadingState();

        } catch (error) {
            this.addLog(`❌ 手动更新失败: ${error.message}`, 'error');
            this.showLoadingState(`更新失败: ${error.message}`, 'error');
            setTimeout(() => {
                this.hideLoadingState();
            }, 3000);
        }
    }
}
// 功能增强管理器
class EnhancementManager {
    constructor() {
        this.initEvents();
        this.currentNovelId = '';
    }

    initEvents() {
        // 加载小说信息
        document.getElementById('loadEnhanceInfoBtn').addEventListener('click', () => {
            this.loadNovelInfo();
        });
        
        // 小说ID输入框回车事件
        document.getElementById('enhanceNovelId').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.loadNovelInfo();
            }
        });
        
        // 情节规划器相关事件
        document.getElementById('generateOutlineBtn').addEventListener('click', () => {
            this.generateChapterOutline();
        });
        
        document.getElementById('generateStoryArcBtn').addEventListener('click', () => {
            this.generateStoryArc();
        });
        
        // 风格迁移相关事件
        document.getElementById('transferStyleBtn').addEventListener('click', () => {
            this.transferStyle();
        });
        
        document.getElementById('loadChapterForStyleBtn').addEventListener('click', () => {
            this.loadChapterContent('style');
        });
        
        // 对话优化相关事件
        document.getElementById('optimizeDialogueBtn').addEventListener('click', () => {
            this.optimizeDialogue();
        });
        
        document.getElementById('loadCharacterForDialogueBtn').addEventListener('click', () => {
            this.loadCharacterSettings();
        });
        
        document.getElementById('loadChapterForDialogueBtn').addEventListener('click', () => {
            this.loadChapterContent('dialogue');
        });
        
        // 内容审查相关事件
        document.getElementById('moderateContentBtn').addEventListener('click', () => {
            this.moderateContent();
        });
        
        document.getElementById('loadChapterForModerateBtn').addEventListener('click', () => {
            this.loadChapterContent('moderate');
        });
    }
    
    async loadNovelInfo() {
        const novelId = document.getElementById('enhanceNovelId').value.trim();
        if (!novelId) {
            Utils.showStatus('enhanceInfo', '请输入小说ID', 'warning');
            return;
        }
        
        this.currentNovelId = novelId;
        
        try {
            const response = await fetch(`${API_BASE}/novels/${novelId}/info`);
            if (!response.ok) throw new Error('获取小说信息失败');
            
            const info = await response.json();
            
            let infoText = `📊 小说 ${novelId} 信息：\n`;
            infoText += `➡️ 当前章节：${info.chapters.latest_chapter_file || 0} 章\n`;
            infoText += `📁 章节文件：${info.chapters.total_chapters || 0} 个\n`;
            infoText += `💾 状态同步：${info.summary.sync_status || '未知'}`;
            
            Utils.showStatus('enhanceInfo', infoText, 'success');
        } catch (error) {
            Utils.showStatus('enhanceInfo', `获取小说信息失败: ${error.message}`, 'error');
        }
    }
    
    async generateChapterOutline() {
        const novelId = document.getElementById('enhanceNovelId').value.trim();
        const currentChapter = parseInt(document.getElementById('currentChapterNum').value) || 0;
        const modelName = document.getElementById('enhanceModelSelect').value;
        
        if (!novelId) {
            alert('请输入小说ID');
            return;
        }
        
        try {
            this.showLoading('outlineResult', '正在生成章节大纲...');
            
            const response = await fetch(`${API_BASE}/generate/outline`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    novel_id: novelId,
                    current_chapter: currentChapter,
                    model_name: modelName
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || '生成失败');
            }
            
            const result = await response.json();
            document.getElementById('outlineResult').innerText = result.outline;
        } catch (error) {
            document.getElementById('outlineResult').innerText = `生成失败: ${error.message}`;
        } finally {
            this.hideLoading('outlineResult');
        }
    }
    
    async generateStoryArc() {
        const novelId = document.getElementById('enhanceNovelId').value.trim();
        const modelName = document.getElementById('enhanceModelSelect').value;
        
        if (!novelId) {
            alert('请输入小说ID');
            return;
        }
        
        try {
            this.showLoading('outlineResult', '正在生成故事弧线...');
            
            const response = await fetch(`${API_BASE}/generate/story-arc`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    novel_id: novelId,
                    model_name: modelName
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || '生成失败');
            }
            
            const result = await response.json();
            
            let storyArcText = '=== 故事弧线规划 ===\n\n';
            if (result.story_summary) storyArcText += `📝 故事梗概：\n${result.story_summary}\n\n`;
            if (result.plot_nodes) storyArcText += `🎭 主要情节节点：\n${result.plot_nodes}\n\n`;
            if (result.chapter_plan) storyArcText += `📚 章节规划：\n${result.chapter_plan}\n\n`;
            if (result.character_arc) storyArcText += `👤 角色成长弧线：\n${result.character_arc}\n\n`;
            if (result.themes_conflicts) storyArcText += `💡 主题和核心冲突：\n${result.themes_conflicts}\n`;
            
            if (!storyArcText || storyArcText === '=== 故事弧线规划 ===\n\n') {
                storyArcText = result.raw_result || '生成结果不可用';
            }
            
            document.getElementById('outlineResult').innerText = storyArcText;
        } catch (error) {
            document.getElementById('outlineResult').innerText = `生成失败: ${error.message}`;
        } finally {
            this.hideLoading('outlineResult');
        }
    }
    
    async transferStyle() {
        const content = document.getElementById('styleContent').value.trim();
        const stylePrompt = document.getElementById('stylePrompt').value.trim();
        const modelName = document.getElementById('enhanceModelSelect').value;
        
        if (!content) {
            alert('请输入需要转换风格的内容');
            return;
        }
        
        if (!stylePrompt) {
            alert('请输入目标风格描述');
            return;
        }
        
        try {
            this.showLoading('styleResult', '正在进行风格转换...');
            
            const response = await fetch(`${API_BASE}/transfer/style`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: content,
                    style_prompt: stylePrompt,
                    model_name: modelName
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || '风格转换失败');
            }
            
            const result = await response.json();
            document.getElementById('styleResult').innerText = result.styled_content;
        } catch (error) {
            document.getElementById('styleResult').innerText = `风格转换失败: ${error.message}`;
        } finally {
            this.hideLoading('styleResult');
        }
    }
    
    async optimizeDialogue() {
        const dialogue = document.getElementById('dialogueContent').value.trim();
        const characterProfilesText = document.getElementById('characterProfiles').value.trim();
        const modelName = document.getElementById('enhanceModelSelect').value;
        
        if (!dialogue) {
            alert('请输入需要优化的对话内容');
            return;
        }
        
        if (!characterProfilesText) {
            alert('请输入人物设定JSON');
            return;
        }
        
        try {
            // 尝试解析人物设定JSON
            const characterProfiles = JSON.parse(characterProfilesText);
            
            this.showLoading('dialogueResult', '正在优化对话...');
            
            const response = await fetch(`${API_BASE}/optimize/dialogue`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    dialogue: dialogue,
                    character_profiles: characterProfiles,
                    model_name: modelName
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || '对话优化失败');
            }
            
            const result = await response.json();
            document.getElementById('dialogueResult').innerText = result.optimized_dialogue;
        } catch (error) {
            document.getElementById('dialogueResult').innerText = `对话优化失败: ${error.message}`;
        } finally {
            this.hideLoading('dialogueResult');
        }
    }
    
    async moderateContent() {
        const content = document.getElementById('moderateContent').value.trim();
        const autoFix = document.getElementById('autoFixContent').checked;
        const modelName = document.getElementById('enhanceModelSelect').value;
        
        if (!content) {
            alert('请输入需要审查的内容');
            return;
        }
        
        try {
            this.showLoading('moderateResult', '正在审查内容...');
            
            const response = await fetch(`${API_BASE}/moderate/content`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: content,
                    model_name: modelName
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || '内容审查失败');
            }
            
            const result = await response.json();
            
            let moderateText = '=== 内容审查结果 ===\n\n';
            moderateText += `审查结果：${result.moderation_result}\n\n`;
            moderateText += `是否存在问题：${result.has_issues ? '是' : '否'}`;
            
            // 如果有问题且选择了自动修正
            if (result.has_issues && autoFix) {
                moderateText += '\n\n=== 自动修正内容 ===\n';
                
                // 调用增强功能的综合API进行修正
                const enhanceResponse = await fetch(`${API_BASE}/enhance/chapter`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        content: content,
                        options: {
                            moderate_content: true,
                            auto_fix_issues: true
                        },
                        model_name: modelName
                    })
                });
                
                if (enhanceResponse.ok) {
                    const enhanceResult = await enhanceResponse.json();
                    moderateText += enhanceResult.final_content;
                } else {
                    moderateText += '自动修正失败';
                }
            }
            
            document.getElementById('moderateResult').innerText = moderateText;
        } catch (error) {
            document.getElementById('moderateResult').innerText = `内容审查失败: ${error.message}`;
        } finally {
            this.hideLoading('moderateResult');
        }
    }
    
    async loadChapterContent(type) {
        const novelId = document.getElementById('enhanceNovelId').value.trim();
        
        if (!novelId) {
            alert('请先输入小说ID并加载信息');
            return;
        }
        
        try {
            // 获取小说信息以确定最新章节
            const infoResponse = await fetch(`${API_BASE}/novels/${novelId}/info`);
            if (!infoResponse.ok) throw new Error('获取小说信息失败');
            
            const info = await infoResponse.json();
            const latestChapter = info.chapters.latest_chapter_file || 0;
            
            if (latestChapter === 0) {
                throw new Error('没有找到可用的章节内容');
            }
            
            // 让用户选择要加载的章节
            const chapterToLoad = prompt(`请输入要加载的章节号 (1-${latestChapter})`, latestChapter);
            if (!chapterToLoad || isNaN(chapterToLoad) || parseInt(chapterToLoad) < 1 || parseInt(chapterToLoad) > latestChapter) {
                throw new Error('请输入有效的章节号');
            }
            
            // 这里假设我们有一个API可以获取章节内容
            // 实际项目中可能需要根据后端实现调整
            alert('章节内容加载功能需要后端支持相应的API');
            
            // 示例：如果有API的话，这里应该是类似这样的代码
            /*
            const chapterResponse = await fetch(`${API_BASE}/novels/${novelId}/chapters/${chapterToLoad}`);
            if (!chapterResponse.ok) throw new Error('获取章节内容失败');
            
            const chapterData = await chapterResponse.json();
            
            if (type === 'style') {
                document.getElementById('styleContent').value = chapterData.content;
            } else if (type === 'dialogue') {
                document.getElementById('dialogueContent').value = chapterData.content;
            } else if (type === 'moderate') {
                document.getElementById('moderateContent').value = chapterData.content;
            }
            */
        } catch (error) {
            alert(`加载章节内容失败: ${error.message}`);
        }
    }
    
    async loadCharacterSettings() {
        const novelId = document.getElementById('enhanceNovelId').value.trim();
        
        if (!novelId) {
            alert('请先输入小说ID并加载信息');
            return;
        }
        
        try {
            // 获取小说的人物设定
            // 这里假设我们有一个API可以获取最新的人物设定
            alert('加载人物设定功能需要后端支持相应的API');
            
            // 示例：如果有API的话，这里应该是类似这样的代码
            /*
            const response = await fetch(`${API_BASE}/settings/${novelId}/character/latest`);
            if (!response.ok) throw new Error('获取人物设定失败');
            
            const result = await response.json();
            document.getElementById('characterProfiles').value = JSON.stringify(result.content, null, 2);
            */
        } catch (error) {
            alert(`加载人物设定失败: ${error.message}`);
        }
    }
    
    showLoading(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `<div style="text-align: center; padding: 20px;"><span class="loading"></span>${message}</div>`;
        }
    }
    
    hideLoading(elementId) {
        // 这个方法留空，因为我们直接在结果中显示内容，不需要单独隐藏加载状态
    }
}

// 应用初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查API连接
    fetch(`${API_BASE}/health`)
        .then(response => {
            if (!response.ok) {
                throw new Error('API服务未启动');
            }
            console.log('API连接正常');
        })
        .catch(error => {
            Utils.showError(`API连接失败: ${error.message}`);
        });

    // 初始化各个管理器
    new TabManager();
    new TemplateManager();
    new BatchGenerator();
    new SettingsManager();
    // 添加EnhancementManager实例化
    new EnhancementManager();
    console.log('小说生成系统前端已启动');
});

// 设定管理器
class SettingsManager {
    constructor() {
        this.currentNovelId = '';
        this.characterVersions = [];
        this.worldVersions = [];
        this.currentCharacterVersion = '';
        this.currentWorldVersion = '';
        this.initEvents();
    }

    initEvents() {
        // 加载设定按钮
        document.getElementById('loadSettingsBtn').addEventListener('click', () => {
            this.loadSettings();
        });

        // 版本选择变化
        document.getElementById('characterVersionSelect').addEventListener('change', (e) => {
            this.loadCharacterSettings(e.target.value);
        });

        document.getElementById('worldVersionSelect').addEventListener('change', (e) => {
            this.loadWorldSettings(e.target.value);
        });

        // 新建按钮
        document.getElementById('newCharacterBtn').addEventListener('click', () => {
            this.createNewCharacterVersion();
        });

        document.getElementById('newWorldBtn').addEventListener('click', () => {
            this.createNewWorldVersion();
        });

        // 保存按钮
        document.getElementById('saveCharacterBtn').addEventListener('click', () => {
            this.saveCharacterSettings();
        });

        document.getElementById('saveWorldBtn').addEventListener('click', () => {
            this.saveWorldSettings();
        });

        // 小说ID输入框回车事件
        document.getElementById('settingsNovelId').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.loadSettings();
            }
        });
    }

    async loadSettings() {
        const novelId = document.getElementById('settingsNovelId').value.trim();
        if (!novelId) {
            this.showSettingsInfo('请输入小说ID', 'warning');
            return;
        }

        this.currentNovelId = novelId;

        try {
            // 获取设定文件列表
            const response = await fetch(`${API_BASE}/settings/${novelId}`);
            if (!response.ok) throw new Error('加载设定失败');

            const result = await response.json();
            this.characterVersions = result.character_versions || [];
            this.worldVersions = result.world_versions || [];

            // 更新版本选择框
            this.updateVersionSelects();

            // 加载最新版本的设定
            if (this.characterVersions.length > 0) {
                const latestCharacter = Math.max(...this.characterVersions.map(v => v.version));
                this.loadCharacterSettings(latestCharacter.toString().padStart(3, '0'));
            }

            if (this.worldVersions.length > 0) {
                const latestWorld = Math.max(...this.worldVersions.map(v => v.version));
                this.loadWorldSettings(latestWorld.toString().padStart(2, '0'));
            }

            this.showSettingsInfo(`✅ 找到小说 ${novelId}\n👤 人物设定: ${this.characterVersions.length}个版本\n🌍 世界设定: ${this.worldVersions.length}个版本`, 'success');

        } catch (error) {
            this.showSettingsInfo(`❌ 加载失败: ${error.message}`, 'error');
        }
    }

    updateVersionSelects() {
        // 更新人物设定版本选择框
        const characterSelect = document.getElementById('characterVersionSelect');
        if (!characterSelect) {
            console.error('characterVersionSelect元素不存在');
            return;
        }
        characterSelect.innerHTML = '<option value="">选择版本...</option>';

        this.characterVersions.forEach(version => {
            const option = new Option(
                `版本 ${version.version.toString().padStart(3, '0')} (${version.filename})`,
                version.version.toString().padStart(3, '0')
            );
            characterSelect.appendChild(option);
        });

        // 更新世界设定版本选择框
        const worldSelect = document.getElementById('worldVersionSelect');
        if (!worldSelect) {
            console.error('worldVersionSelect元素不存在');
            return;
        }
        worldSelect.innerHTML = '<option value="">选择版本...</option>';

        this.worldVersions.forEach(version => {
            const option = new Option(
                `版本 ${version.version.toString().padStart(2, '0')} (${version.filename})`,
                version.version.toString().padStart(2, '0')
            );
            worldSelect.appendChild(option);
        });
    }

    async loadCharacterSettings(version) {
        if (!version || !this.currentNovelId) return;

        try {
            const response = await fetch(`${API_BASE}/settings/${this.currentNovelId}/character/${version}`);
            if (!response.ok) throw new Error('加载人物设定失败');

            const result = await response.json();
            document.getElementById('characterSettings').value = JSON.stringify(result.content, null, 2);
            this.currentCharacterVersion = version;

            // 更新选择框
            document.getElementById('characterVersionSelect').value = version;

        } catch (error) {
            Utils.showError(`加载人物设定失败: ${error.message}`);
        }
    }

    async loadWorldSettings(version) {
        if (!version || !this.currentNovelId) return;

        try {
            const response = await fetch(`${API_BASE}/settings/${this.currentNovelId}/world/${version}`);
            if (!response.ok) throw new Error('加载世界设定失败');

            const result = await response.json();
            document.getElementById('worldSettings').value = JSON.stringify(result.content, null, 2);
            this.currentWorldVersion = version;

            // 更新选择框
            document.getElementById('worldVersionSelect').value = version;

        } catch (error) {
            Utils.showError(`加载世界设定失败: ${error.message}`);
        }
    }

    async createNewCharacterVersion() {
        if (!this.currentNovelId) {
            Utils.showError('请先加载小说设定');
            return;
        }

        try {
            // 获取当前内容
            const currentContent = document.getElementById('characterSettings').value.trim();
            if (!currentContent) {
                Utils.showError('当前没有人物设定内容可复制');
                return;
            }

            // 创建新版本
            const response = await fetch(`${API_BASE}/settings/${this.currentNovelId}/character/new`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: JSON.parse(currentContent),
                    base_version: this.currentCharacterVersion
                })
            });

            if (!response.ok) throw new Error('创建新版本失败');

            const result = await response.json();

            // 重新加载设定列表
            await this.loadSettings();

            // 自动选择新创建的版本
            this.loadCharacterSettings(result.new_version);

            Utils.showStatus('settingsInfo', `✅ 创建人物设定版本 ${result.new_version} 成功`, 'success');

        } catch (error) {
            Utils.showError(`创建新版本失败: ${error.message}`);
        }
    }

    async createNewWorldVersion() {
        if (!this.currentNovelId) {
            Utils.showError('请先加载小说设定');
            return;
        }

        try {
            // 获取当前内容
            const currentContent = document.getElementById('worldSettings').value.trim();
            if (!currentContent) {
                Utils.showError('当前没有世界设定内容可复制');
                return;
            }

            // 创建新版本
            const response = await fetch(`${API_BASE}/settings/${this.currentNovelId}/world/new`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: JSON.parse(currentContent),
                    base_version: this.currentWorldVersion
                })
            });

            if (!response.ok) throw new Error('创建新版本失败');

            const result = await response.json();

            // 重新加载设定列表
            await this.loadSettings();

            // 自动选择新创建的版本
            this.loadWorldSettings(result.new_version);

            Utils.showStatus('settingsInfo', `✅ 创建世界设定版本 ${result.new_version} 成功`, 'success');

        } catch (error) {
            Utils.showError(`创建新版本失败: ${error.message}`);
        }
    }

    async saveCharacterSettings() {
        if (!this.currentNovelId || !this.currentCharacterVersion) {
            Utils.showError('请先选择要保存的版本');
            return;
        }

        try {
            const content = document.getElementById('characterSettings').value.trim();
            if (!content) {
                Utils.showError('人物设定内容不能为空');
                return;
            }

            // 验证JSON格式
            const parsedContent = JSON.parse(content);

            const response = await fetch(`${API_BASE}/settings/${this.currentNovelId}/character/${this.currentCharacterVersion}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: parsedContent })
            });

            if (!response.ok) throw new Error('保存失败');

            Utils.showStatus('settingsInfo', '✅ 人物设定保存成功', 'success');

        } catch (error) {
            if (error instanceof SyntaxError) {
                Utils.showError('JSON格式错误，请检查语法');
            } else {
                Utils.showError(`保存失败: ${error.message}`);
            }
        }
    }

    async saveWorldSettings() {
        if (!this.currentNovelId || !this.currentWorldVersion) {
            Utils.showError('请先选择要保存的版本');
            return;
        }

        try {
            const content = document.getElementById('worldSettings').value.trim();
            if (!content) {
                Utils.showError('世界设定内容不能为空');
                return;
            }

            // 验证JSON格式
            const parsedContent = JSON.parse(content);

            const response = await fetch(`${API_BASE}/settings/${this.currentNovelId}/world/${this.currentWorldVersion}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: parsedContent })
            });

            if (!response.ok) throw new Error('保存失败');

            Utils.showStatus('settingsInfo', '✅ 世界设定保存成功', 'success');

        } catch (error) {
            if (error instanceof SyntaxError) {
                Utils.showError('JSON格式错误，请检查语法');
            } else {
                Utils.showError(`保存失败: ${error.message}`);
            }
        }
    }

    showSettingsInfo(message, type = 'info') {
        const infoDiv = document.getElementById('settingsInfo');
        infoDiv.className = `novel-info show ${type}`;
        infoDiv.textContent = message;

        // 3秒后隐藏（除非是成功状态）
        if (type !== 'success') {
            setTimeout(() => {
                infoDiv.classList.remove('show');
            }, 3000);
        }
    }
}