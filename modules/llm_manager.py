import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
import requests
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === 全局大模型配置获取器 ===
# 🚨 重要提醒：请勿修改以下模型配置，这些是用户自定义的固定配置 🚨
class LLMConfigManager:
    @staticmethod
    def get_config(model_name: str) -> Dict[str, Any]:
        configs = {
            "deepseek_chat": {
                "provider": "openai",
                "model": "deepseek-chat",
                "api_key": os.getenv("DEEPSEEK_API_KEY"),
                "base_url": "https://api.deepseek.com/v1",
                "temperature": 0.7
            },
            "deepseek_reasoner": {
                "provider": "openai",
                "model": "deepseek-reasoner", 
                "api_key": os.getenv("DEEPSEEK_API_KEY"),
                "base_url": "https://api.deepseek.com/v1",
                "temperature": 0.7
            },
            "dsf5": {
                "provider": "openai",
                "model": os.getenv("DSF5_API_MODEL"),
                "api_key": os.getenv("DSF5_API_KEY"),
                "base_url": os.getenv("DSF5_API_URL"),
                "temperature": 0.7
            },
            "openai_gpt4": {
                "provider": "openai",
                "model": "gpt-4",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": None,
                "temperature": 0.7
            },
            "openai_gpt35": {
                "provider": "openai", 
                "model": "gpt-3.5-turbo",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": None,
                "temperature": 0.7
            },
            "anthropic_claude": {
                "provider": "anthropic",
                "model": "claude-3-sonnet-20240229",
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "base_url": None,
                "temperature": 0.7
            },
            "google_gemini": {
                "provider": "google",
                "model": "gemini-pro",
                "api_key": os.getenv("GOOGLE_API_KEY"),
                "base_url": None,
                "temperature": 0.7
            }
        }
        # 默认返回deepseek_chat模型
        return configs.get(model_name, configs["deepseek_chat"])
# === 全局大模型调用器 ===
class LLMCaller:
    @staticmethod
    # 在 LLMCaller.call 方法中添加特殊处理
    def call(
        messages: List[Dict[str, str]],
        model_name: str = "deepseek_chat",
        memory: Optional[Any] = None,
        temperature: Optional[float] = None
    ) -> str:
        config = LLMConfigManager.get_config(model_name)
        
        if temperature is not None:
            config["temperature"] = temperature
            
        # 特殊处理 Open WebUI 平台 (DSF5)
        if model_name == "dsf5":
            # 直接使用 requests 库调用 API，避免 LangChain 的默认行为
            import requests
            
            # 构建请求体 - 为dsf5模型设置正确的temperature值为1.0
            payload = {
                "model": config["model"],
                "messages": messages,
                "temperature": 1.0  # 强制设置为支持的值
            }
            
            # 设置请求头
            headers = {
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json"
            }
            
            # 构建完整的 API URL
            api_url = f"{config['base_url']}/chat/completions"
            
            try:
                # 发送请求
                response = requests.post(api_url, json=payload, headers=headers)
                response.raise_for_status()  # 如果响应状态码不是 200，抛出异常
                
                # 解析响应
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except requests.exceptions.RequestException as e:
                print(f"调用 Open WebUI API 失败: {e}")
                # 如果有响应内容，打印出来以便调试
                if hasattr(e, 'response') and e.response is not None:
                    print(f"响应状态码: {e.response.status_code}")
                    print(f"响应内容: {e.response.text}")
                raise

        # 根据provider创建对应的LLM实例
        if config["provider"] == "openai":
            from langchain_openai import ChatOpenAI
            llm_params = {
                "model": config["model"],
                "api_key": config["api_key"],
                "temperature": config["temperature"]
            }
            if config["base_url"]:
                llm_params["base_url"] = config["base_url"]
            llm = ChatOpenAI(**llm_params)
        elif config["provider"] == "anthropic":
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(
                model=config["model"],
                api_key=config["api_key"],
                temperature=config["temperature"]
            )
        elif config["provider"] == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model=config["model"],
                google_api_key=config["api_key"],
                temperature=config["temperature"]
            )
        else:
            raise ValueError(f"Unsupported provider: {config['provider']}")
        
        # 后续代码保持不变
        # 如果有记忆，使用对话链
        if memory:
            from langchain.chains import ConversationChain
            chain = ConversationChain(llm=llm, memory=memory, verbose=False)
            # 将messages转换为单个输入
            user_input = messages[-1]["content"] if messages else ""
            return chain.predict(input=user_input)
        else:
            # 直接调用LLM
            from langchain_core.messages import HumanMessage, SystemMessage
            lang_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    lang_messages.append(SystemMessage(content=msg["content"]))
                else:
                    lang_messages.append(HumanMessage(content=msg["content"]))
            
            response = llm.invoke(lang_messages)
            return response.content

