import requests
import json
import logging
from datetime import datetime, timedelta
import os
import sys
import time
import threading
from itertools import cycle

CONFIG_FILE = "config.json"  # 配置文件路径

class AIChat:
    def __init__(self, model="gpt-4o-mini"):
        # 加载配置文件
        config = self.load_config()
        self.default_model = config.get("default_model", model)
        
        # 备用模型配置
        self.fallback_models = {
            "gpt-4o-mini": ["4o-mini-backup", "4o-mini-backup2", "4o-mini-pro"],
            "DeepSeek": ["DeepSeekPro", "DeepSeek1.0", "DeepSeek2.0", "DeepSeek3.0"],
            "DeepSeekPro": ["DeepSeek", "DeepSeek1.0", "DeepSeek2.0", "DeepSeek3.0"],
            "DeepSeek1.0": ["DeepSeek", "DeepSeekPro", "DeepSeek2.0", "DeepSeek3.0"],
            "DeepSeek2.0": ["DeepSeek", "DeepSeekPro", "DeepSeek1.0", "DeepSeek3.0"],
            "DeepSeek3.0": ["DeepSeek", "DeepSeekPro", "DeepSeek1.0", "DeepSeek2.0"],
            "Ultra": ["Max", "ZhipuAI"],
            "Max": ["Ultra", "ZhipuAI"],
            "ZhipuAI": ["Ultra", "Max"]
        }
        
        # 模型切换历史
        self.switch_history = []
        
        # 最大重试次数
        self.max_retries = 3
        
        self.api_urls = {
            "AIchat": "https://api.milorapart.top/api/AIchat?apiKey=58ea3eb01638af6d275aa82a8c8d538f",
            "KimiChat": "https://api.milorapart.top/api/kimichat?apiKey=1876cac3abe4a597a3cab324e976d2cd",
            "DeepSeek": "https://api.milorapart.top/api/deepseek?apiKey=dd2e973902e958e6ac83a9058ce2dcfd",
            "Doubao": "https://api.qster.top/API/v2/doubao",
            "DeepSeekPro": "https://api.qster.top/API/v2/DeepSeek",
            "4o-mini-backup": "https://api.qster.top/API/v1/chat",
            "ZhipuAI": "https://api.qster.top/API/v1/zhipuAI",
            "Ultra": "https://api.qster.top/API/v1/4.0Ultra",
            "Max": "https://api.qster.top/API/v1/generalv3.5",
            "Moonshot": "https://api.qster.top/API/v1/MoonshotAi",
            "Moli": "http://api.yujn.cn/api/moli.php",
            "XFAi": "https://api.pearktrue.cn/api/xfai",
            "FF": "http://cp.2s.ink/api/ff.php",
            "SuwanAI": "https://api.suyanw.cn/api/dialog.php",
            "KuakeAI": "https://api.317ak.com/API/AI/kuakeai/kuakeai.php",
            "4o-mini-backup2": "https://api.317ak.com/API/AI/GPT/chatgpt2.0.php",
            "4o-mini-pro": "https://api.317ak.com/API/AI/GPT/chatgpt.php",
            "Feifei": "https://api.317ak.com/API/AI/ffai/ff.php",
            "Phi4": "https://api.317ak.com/API/AI/phi/phi-4.php",
            "SizhiAI": "https://api.317ak.com/API/AI/szai/szai.php",
            "QingmengAI": "https://api.317ak.com/API/AI/qmzygpt/qmzygpt.php",
            "DeepSeek1.0": "https://api.317ak.com/API/AI/deepseek/deepseek.php",
            "DeepSeek2.0": "https://api.317ak.com/API/AI/deepseek/deepseek5.0.php",
            "DeepSeek3.0": "https://api.317ak.com/API/AI/deepseek/deepseek3.0.php",
            "SmartAI": "https://wanghun.top/api/v5/smartai.php",
            "XianliaoAI": "https://api.xdau.cn/api/xd-xianliao"
        }
        self.current_api = "AIchat"
        self.headers = {
            "Content-Type": "application/json"
        }
        self.model = self.default_model
        self.messages = []
        self.logger = setup_logger()
        self.deepseek_pro_config = {
            "sessionid": "",
            "character": "",
            "think": "true",
            "use_enhance": "false",
            "stream": "false",
            "type": "json"
        }
        self.deepseek_1_config = {
            "model": "deepseek-chat"  # 默认为普通模型
        }
        self.deepseek_2_config = {
            "qq": "10086"  # 默认QQ号
        }
        self.deepseek_3_config = {
            "qq": "10086"  # 默认QQ号
        }
        self.ultra_config = {
            "sessionid": "",
            "character": "",
            "type": "json"
        }
        self.mini_pro_config = {
            "qq": "10086"  # 默认QQ号
        }
        self.sizhi_config = {
            "qq": "10086"  # 默认QQ号
        }
        self.available_models = {
            "1": "gpt-4o-mini (GPT-4)",
            "2": "KimiChat (Kimi AI)",
            "3": "DeepSeek (DeepSeek AI)",
            "4": "gemini-1.5 (谷歌 Gemini)",
            "5": "gemini-flash (闪电版)",
            "6": "command-r (指令优化版)",
            "7": "claude-haiku (Claude AI)",
            "8": "llama-3 (Llama3)",
            "9": "Doubao (豆包AI)",
            "10": "DeepSeekPro (DeepSeek高级版)",
            "11": "4o-mini-backup (GPT-4备用)",
            "12": "ZhipuAI (智谱AI)",
            "13": "Ultra (星火4.0Ultra)",
            "14": "Max (星火Max)",
            "15": "Moonshot (Moonshot AI)",
            "16": "Moli (茉莉机器人)",
            "17": "XFAi (星火大模型)",
            "18": "FF (浮生AI)",
            "19": "SuwanAI (素颜AI)",
            "20": "KuakeAI (夸克AI)",
            "21": "4o-mini-backup2 (GPT-4备用2)",
            "22": "4o-mini-pro (GPT-4高级版)",
            "23": "Feifei (菲菲AI)",
            "24": "Phi4 (微软Phi-4)",
            "25": "SizhiAI (思知AI)",
            "26": "QingmengAI (倾梦5.0)",
            "27": "DeepSeek1.0 (DeepSeek 1.0)",
            "28": "DeepSeek2.0 (DeepSeek 2.0)",
            "29": "DeepSeek3.0 (DeepSeek 3.0)",
            "30": "SmartAI (智能AI)",
            "31": "XianliaoAI (闲聊AI)"
        }

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
        return {}

    def save_config(self, config):
        """保存配置文件"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {str(e)}")
            return False

    def set_default_model(self):
        """设置默认AI模型"""
        print("\n设置默认AI模型:")
        print("当前可用模型：")
        
        # 显示所有可用模型
        for key, model_name in self.available_models.items():
            if model_name.startswith(self.default_model):
                print(f"{key}. {model_name} [当前默认]")
            else:
                print(f"{key}. {model_name}")
        
        choice = input("\n请选择要设置为默认的模型编号: ").strip()
        
        if choice in self.available_models:
            full_model_name = self.available_models[choice]
            new_default_model = full_model_name.split(" (")[0]
            
            # 保存到配置文件
            config = self.load_config()
            config["default_model"] = new_default_model
            if self.save_config(config):
                self.default_model = new_default_model
                print(f"\n默认模型已设置为: {full_model_name}")
                return True
            else:
                print("\n保存配置失败，默认模型未更改")
                return False
        else:
            print("\n无效的选择，默认模型未更改")
            return False

    def configure_deepseek_pro(self):
        print("\nDeepSeek高级版配置:")
        print("1. 设置角色描述")
        print("2. 开关深度思考")
        print("3. 开关联网功能")
        print("4. 设置会话ID")
        print("5. 开始使用")
        
        while True:
            choice = input("\n请选择配置项 (1-5): ").strip()
            
            if choice == "1":
                character = input("请输入角色描述: ").strip()
                self.deepseek_pro_config["character"] = character
                print("角色设定已更新")
            
            elif choice == "2":
                think = input("是否开启深度思考 (y/n): ").strip().lower()
                self.deepseek_pro_config["think"] = "true" if think == 'y' else "false"
                print(f"深度思考已{'开启' if think == 'y' else '关闭'}")
            
            elif choice == "3":
                enhance = input("是否开启联网功能 (y/n): ").strip().lower()
                self.deepseek_pro_config["use_enhance"] = "true" if enhance == 'y' else "false"
                print(f"联网功能已{'开启' if enhance == 'y' else '关闭'}")
            
            elif choice == "4":
                sessionid = input("请输入会话ID (直接回车使用默认): ").strip()
                self.deepseek_pro_config["sessionid"] = sessionid
                print("会话ID已更新")
            
            elif choice == "5":
                print("\n开始使用 DeepSeek 高级版...")
                break
            
            else:
                print("无效的选择，请重试")

    def configure_mini_pro(self):
        print("\nGPT-4o-mini高级版配置:")
        print("1. 设置QQ号 (用于上下文跟踪)")
        print("2. 开始使用")
        
        while True:
            choice = input("\n请选择配置项 (1-2): ").strip()
            
            if choice == "1":
                qq = input("请输入QQ号 (用于维持上下文，默认10086): ").strip()
                if qq:
                    self.mini_pro_config["qq"] = qq
                else:
                    self.mini_pro_config["qq"] = "10086"
                print(f"QQ号已设置为: {self.mini_pro_config['qq']}")
            
            elif choice == "2":
                print("\n开始使用GPT-4o-mini高级版...")
                break
            
            else:
                print("无效的选择，请重试")

    def configure_sizhi(self):
        print("\n思知AI配置:")
        print("1. 设置QQ号 (用于上下文跟踪)")
        print("2. 开始使用")
        
        while True:
            choice = input("\n请选择配置项 (1-2): ").strip()
            
            if choice == "1":
                qq = input("请输入QQ号 (用于维持上下文，默认10086): ").strip()
                if qq:
                    self.sizhi_config["qq"] = qq
                else:
                    self.sizhi_config["qq"] = "10086"
                print(f"QQ号已设置为: {self.sizhi_config['qq']}")
            
            elif choice == "2":
                print("\n开始使用思知AI...")
                break
            
            else:
                print("无效的选择，请重试")

    def configure_ultra(self):
        print("\n星火4.0Ultra配置:")
        print("1. 设置角色描述")
        print("2. 设置会话ID")
        print("3. 设置返回格式(json/text)")
        print("4. 开始使用")
        
        while True:
            choice = input("\n请选择配置项 (1-4): ").strip()
            
            if choice == "1":
                character = input("请输入角色描述 (例如: 是一个导演): ").strip()
                self.ultra_config["character"] = character
                print("角色设定已更新")
            
            elif choice == "2":
                sessionid = input("请输入会话ID (直接回车使用默认): ").strip()
                self.ultra_config["sessionid"] = sessionid
                print("会话ID已更新")
            
            elif choice == "3":
                type_choice = input("请选择返回格式 (1: json, 2: text): ").strip()
                if type_choice == "1":
                    self.ultra_config["type"] = "json"
                elif type_choice == "2":
                    self.ultra_config["type"] = "text"
                print(f"返回格式已设置为: {self.ultra_config['type']}")
            
            elif choice == "4":
                print("\n开始使用星火4.0Ultra...")
                break
            
            else:
                print("无效的选择，请重试")

    def configure_deepseek_1(self):
        print("\nDeepSeek1.0配置:")
        print("1. 选择模型类型")
        print("2. 开始使用")
        
        while True:
            choice = input("\n请选择配置项 (1-2): ").strip()
            
            if choice == "1":
                model_type = input("请选择模型类型 (1: 普通模型 deepseek-chat, 2: 推理模型 deepseek-reasoner): ").strip()
                if model_type == "1":
                    self.deepseek_1_config["model"] = "deepseek-chat"
                    print("已设置为普通模型")
                elif model_type == "2":
                    self.deepseek_1_config["model"] = "deepseek-reasoner"
                    print("已设置为推理模型")
                else:
                    print("无效选择，使用默认普通模型")
            
            elif choice == "2":
                print("\n开始使用DeepSeek1.0...")
                break
            
            else:
                print("无效的选择，请重试")

    def configure_deepseek_2(self):
        print("\nDeepSeek2.0配置:")
        print("1. 设置QQ号")
        print("2. 开始使用")
        
        while True:
            choice = input("\n请选择配置项 (1-2): ").strip()
            
            if choice == "1":
                qq = input("请输入QQ号: ").strip()
                if qq:
                    self.deepseek_2_config["qq"] = qq
                    print("QQ号已更新")
                else:
                    print("QQ号不能为空")
            
            elif choice == "2":
                print("\n开始使用DeepSeek2.0...")
                break
            
            else:
                print("无效的选择，请重试")

    def configure_deepseek_3(self):
        print("\nDeepSeek3.0配置:")
        print("1. 设置QQ号")
        print("2. 开始使用")
        
        while True:
            choice = input("\n请选择配置项 (1-2): ").strip()
            
            if choice == "1":
                qq = input("请输入QQ号: ").strip()
                if qq:
                    self.deepseek_3_config["qq"] = qq
                    print("QQ号已更新")
                else:
                    print("QQ号不能为空")
            
            elif choice == "2":
                print("\n开始使用DeepSeek3.0...")
                break
            
            else:
                print("无效的选择，请重试")

    def change_model(self):
        print("\n可用模型：")
        current_model_key = None
        for key, model_name in self.available_models.items():
            if model_name.startswith(self.model):
                current_model_key = key
                break

        for key, model_name in self.available_models.items():
            if key == current_model_key:
                print(f"{key}. {model_name} [当前使用]")
            else:
                print(f"{key}. {model_name}")
        
        choice = input("\n请选择模型编号: ").strip()
        if choice in self.available_models:
            full_model_name = self.available_models[choice]
            self.model = full_model_name.split(" (")[0]
            
            if "KimiChat" in full_model_name:
                self.current_api = "KimiChat"
            elif "DeepSeek" in full_model_name and "高级版" in full_model_name:
                self.current_api = "DeepSeekPro"
                self.configure_deepseek_pro()
            elif "DeepSeek1.0" in full_model_name:
                self.current_api = "DeepSeek1.0"
                self.configure_deepseek_1()
            elif "DeepSeek2.0" in full_model_name:
                self.current_api = "DeepSeek2.0"
                self.configure_deepseek_2()
            elif "DeepSeek3.0" in full_model_name:
                self.current_api = "DeepSeek3.0"
                self.configure_deepseek_3()
            elif "DeepSeek" in full_model_name:
                self.current_api = "DeepSeek"
            elif "Doubao" in full_model_name:
                self.current_api = "Doubao"
            elif "4o-mini-pro" in full_model_name:
                self.current_api = "4o-mini-pro"
                self.configure_mini_pro()
            elif "4o-mini-backup2" in full_model_name:
                self.current_api = "4o-mini-backup2"
            elif "4o-mini-backup" in full_model_name:
                self.current_api = "4o-mini-backup"
            elif "ZhipuAI" in full_model_name:
                self.current_api = "ZhipuAI"
            elif "Ultra" in full_model_name:
                self.current_api = "Ultra"
                self.configure_ultra()
            elif "Max" in full_model_name:
                self.current_api = "Max"
            elif "Moonshot" in full_model_name:
                self.current_api = "Moonshot"
            elif "Moli" in full_model_name:
                self.current_api = "Moli"
            elif "XFAi" in full_model_name:
                self.current_api = "XFAi"
            elif "FF" in full_model_name:
                self.current_api = "FF"
            elif "Phi4" in full_model_name:
                self.current_api = "Phi4"
            elif "SizhiAI" in full_model_name:
                self.current_api = "SizhiAI"
                self.configure_sizhi()
            elif "QingmengAI" in full_model_name:
                self.current_api = "QingmengAI"
            elif "Feifei" in full_model_name:
                self.current_api = "Feifei"
            elif "SuwanAI" in full_model_name:
                self.current_api = "SuwanAI"
            elif "KuakeAI" in full_model_name:
                self.current_api = "KuakeAI"
            elif "SmartAI" in full_model_name:
                self.current_api = "SmartAI"
            elif "XianliaoAI" in full_model_name:
                self.current_api = "XianliaoAI"
            else:
                self.current_api = "AIchat"
                
            print(f"\n已切换到 {full_model_name}")
            return True
        else:
            print("\n无效的选择，保持当前模型")
            return False

    def switch_to_fallback(self, current_model, error_msg):
        """切换到备用模型"""
        if current_model not in self.fallback_models:
            return False, "没有可用的备用模型"
            
        # 获取当前模型的备用模型列表
        fallbacks = self.fallback_models[current_model]
        
        # 记录切换历史
        self.switch_history.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "from_model": current_model,
            "error": error_msg
        })
        
        # 尝试切换到备用模型
        for fallback in fallbacks:
            if fallback not in [h.get("from_model") for h in self.switch_history[-self.max_retries:]]:
                self.model = fallback
                self.current_api = fallback
                return True, f"已切换到备用模型: {fallback}"
                
        return False, "所有备用模型都已尝试"

    def send_message(self, user_input):
        """发送消息并处理响应"""
        # 记录用户输入
        self.logger.info(f"用户输入: {user_input}")
        
        # 添加用户消息到对话历史
        self.messages.append({
            "role": "user",
            "content": user_input
        })
        
        retries = 0
        current_model = self.model
        
        while retries < self.max_retries:
            try:
                api_url = self.api_urls[self.current_api]
                
                if self.current_api == "Moli":
                    api_url = f"{api_url}?msg={user_input}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        content = response.text
                        self.messages.append({
                            "role": "assistant",
                            "content": content
                        })
                        return content
                    else:
                        return "茉莉API响应错误"
                elif self.current_api == "FF":
                    api_url = f"{api_url}?msg={user_input}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        content = response.text
                        self.messages.append({
                            "role": "assistant",
                            "content": content
                        })
                        return content
                    else:
                        return "浮生API响应错误"
                elif self.current_api == "QingmengAI":
                    api_url = f"{api_url}?msg={user_input}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            if result.get("status") == "success" and "data" in result:
                                content = result["data"]
                                self.messages.append({
                                    "role": "assistant",
                                    "content": content
                                })
                                return content
                            else:
                                return f"倾梦AI无法回复: {result.get('message', '未知错误')}"
                        except ValueError:
                            # 如果返回的不是JSON，尝试直接使用文本内容
                            content = response.text
                            if content and "error" not in content.lower():
                                self.messages.append({
                                    "role": "assistant",
                                    "content": content
                                })
                                return content
                            else:
                                return "倾梦AI响应格式错误"
                    else:
                        return "倾梦AI API响应错误"
                elif self.current_api == "SizhiAI":
                    qq = self.sizhi_config.get("qq", "10086")
                    api_url = f"{api_url}?msg={user_input}&qq={qq}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        result = response.json()
                        if result["code"] == 200 and "data" in result:
                            content = result["data"]["fromtext"]
                            self.messages.append({
                                "role": "assistant",
                                "content": content
                            })
                            return content
                        else:
                            return "思知AI无法回复"
                    else:
                        return "思知AI API响应错误"
                elif self.current_api == "Phi4":
                    api_url = f"{api_url}?msg={user_input}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        result = response.json()
                        if "content" in result:
                            content = result["content"]
                            self.messages.append({
                                "role": "assistant",
                                "content": content
                            })
                            return content
                        else:
                            return "Phi-4无法回复"
                    else:
                        return "Phi-4 API响应错误"
                elif self.current_api == "Feifei":
                    api_url = f"{api_url}?msg={user_input}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        content = response.text
                        self.messages.append({
                            "role": "assistant",
                            "content": content
                        })
                        return content
                    else:
                        return "菲菲API响应错误"
                elif self.current_api == "4o-mini-pro":
                    qq = self.mini_pro_config.get("qq", "10086")
                    api_url = f"{api_url}?rm=&qq={qq}&msg={user_input}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        result = response.json()
                        if result["code"] == 1 and "data" in result:
                            content = result["data"]
                            self.messages.append({
                                "role": "assistant",
                                "content": content
                            })
                            return content
                        else:
                            return "GPT-4高级版无法回复"
                    else:
                        return "GPT-4高级版API响应错误"
                elif self.current_api == "4o-mini-backup2":
                    api_url = f"{api_url}?msg={user_input}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        content = response.text
                        # 检查是否有效响应
                        if content and content.strip() != "无有效的回复内容":
                            self.messages.append({
                                "role": "assistant",
                                "content": content
                            })
                            return content
                        else:
                            return "备用2 API无有效响应"
                    else:
                        return "备用2 API响应错误"
                elif self.current_api == "KuakeAI":
                    api_url = f"{api_url}?msg={user_input}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        result = response.json()
                        if result["code"] == 1:
                            content = result["text"]
                            self.messages.append({
                                "role": "assistant",
                                "content": content,
                                "form": result.get("form", "聊天")
                            })
                            return content
                        else:
                            return "夸克AI无法回复"
                    else:
                        return "夸克API响应错误"
                elif self.current_api == "SuwanAI":
                    api_url = f"{api_url}?msg={user_input}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        result = response.json()
                        if result["code"] == "1":
                            content = result["text"]
                            self.messages.append({
                                "role": "assistant",
                                "content": content
                            })
                            return content
                        else:
                            return "素颜AI无法回复"
                    else:
                        return "素颜API响应错误"
                elif self.current_api == "XFAi":
                    api_url = f"{api_url}/?message={user_input}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        result = response.json()
                        if result["code"] == 200:
                            content = result["answer"]
                            self.messages.append({
                                "role": "assistant",
                                "content": content,
                                "model": result.get("model", "星火大模型")
                            })
                            return content
                        else:
                            return "星火AI无法回复"
                    else:
                        return "星火API响应错误"
                elif self.current_api in ["4o-mini-backup", "ZhipuAI", "Ultra", "Max", "Moonshot"]:
                    api_url = f"{api_url}/?msg={user_input}"
                    response = requests.get(api_url)
                elif self.current_api == "DeepSeekPro":
                    params = {
                        "content": user_input,
                        **self.deepseek_pro_config
                    }
                    params = {k: v for k, v in params.items() if v}
                    query_string = "&".join(f"{k}={v}" for k, v in params.items())
                    api_url = f"{api_url}/?{query_string}"
                    response = requests.get(api_url)
                elif self.current_api == "Doubao":
                    api_url = f"{api_url}/?content={user_input}"
                    response = requests.get(api_url)
                elif self.current_api == "DeepSeek1.0":
                    model_param = self.deepseek_1_config.get("model", "deepseek-chat")
                    api_url = f"{api_url}?msg={user_input}&model={model_param}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            if "content" in result:
                                content = result["content"]
                                self.messages.append({
                                    "role": "assistant",
                                    "content": content,
                                    "model": model_param
                                })
                                return content
                            else:
                                return "DeepSeek1.0无法回复"
                        except ValueError:
                            return "DeepSeek1.0响应格式错误"
                    else:
                        return "DeepSeek1.0 API响应错误"
                elif self.current_api == "DeepSeek2.0":
                    qq = self.deepseek_2_config.get("qq", "10086")
                    api_url = f"{api_url}?msg={user_input}&qq={qq}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            if "content" in result:
                                content = result["content"]
                                self.messages.append({
                                    "role": "assistant",
                                    "content": content,
                                    "model": "DeepSeek2.0"
                                })
                                return content
                            else:
                                return "DeepSeek2.0无法回复"
                        except ValueError:
                            return "DeepSeek2.0响应格式错误"
                    else:
                        return "DeepSeek2.0 API响应错误"
                elif self.current_api == "DeepSeek3.0":
                    qq = self.deepseek_3_config.get("qq", "10086")
                    api_url = f"{api_url}?msg={user_input}&qq={qq}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            if "content" in result:
                                content = result["content"]
                                self.messages.append({
                                    "role": "assistant",
                                    "content": content,
                                    "model": "DeepSeek3.0"
                                })
                                return content
                            else:
                                return "DeepSeek3.0无法回复"
                        except ValueError:
                            return "DeepSeek3.0响应格式错误"
                    else:
                        return "DeepSeek3.0 API响应错误"
                elif self.current_api == "SmartAI":
                    api_url = f"{api_url}?msg={user_input}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        try:
                            content = response.text
                            self.messages.append({
                                "role": "assistant",
                                "content": content,
                                "model": "SmartAI"
                            })
                            return content
                        except Exception as e:
                            return f"SmartAI响应错误: {str(e)}"
                    else:
                        return "SmartAI API响应错误"
                elif self.current_api == "XianliaoAI":
                    api_url = f"{api_url}?msg={user_input}"
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        try:
                            content = response.text
                            self.messages.append({
                                "role": "assistant",
                                "content": content,
                                "model": "XianliaoAI"
                            })
                            return content
                        except Exception as e:
                            return f"XianliaoAI响应错误: {str(e)}"
                    else:
                        return "XianliaoAI API响应错误"
                else:
                    if self.current_api == "KimiChat" or self.current_api == "DeepSeek":
                        payload = {
                            "messages": [{
                                "role": "user",
                                "content": user_input
                            }]
                        }
                    else:
                        payload = {
                            "messages": [{
                                "role": "user",
                                "content": user_input
                            }],
                            "model": self.model,
                            "stream": False
                        }
                    response = requests.post(api_url, headers=self.headers, json=payload)
                
                response.raise_for_status()
                
                if self.current_api not in ["Moli", "XFAi", "FF", "SuwanAI", "KuakeAI", "4o-mini-backup2", "4o-mini-pro", "Feifei", "Phi4", "SizhiAI", "QingmengAI"]:
                    result = response.json()
                    
                    if self.current_api == "ZhipuAI":
                        if result["code"] == 200:
                            if result.get("answer"):
                                content = result["answer"]
                                self.messages.append({
                                    "role": "assistant",
                                    "content": content,
                                    "model": result.get("model", "glm-4")
                                })
                                return content
                            else:
                                return "AI 暂时无法回复"
                    elif self.current_api == "4o-mini-backup":
                        if result["code"] == 200 and "choices" in result:
                            content = result["choices"][0]["message"]["content"]
                            if "sessionid" in result and result["sessionid"]:
                                self.messages.append({
                                    "role": "assistant",
                                    "content": content,
                                    "sessionid": result["sessionid"]
                                })
                            else:
                                self.messages.append({
                                    "role": "assistant",
                                    "content": content
                                })
                            return content
                    elif self.current_api == "DeepSeekPro":
                        if result["code"] == 200 and "choices" in result:
                            content = result["choices"][0]["content"]
                            if "sessionid" in result:
                                self.deepseek_pro_config["sessionid"] = result["sessionid"]
                            self.messages.append({
                                "role": "assistant",
                                "content": content
                            })
                            return content
                    elif self.current_api == "Doubao":
                        if result["code"] == 200 and "data" in result:
                            content = result["data"]["reply"]
                            self.messages.append({
                                "role": "assistant",
                                "content": content
                            })
                            return content
                    elif self.current_api == "KimiChat":
                        if "reply" in result:
                            content = result["reply"]
                            self.messages.append({
                                "role": "assistant",
                                "content": content
                            })
                            return content
                    elif self.current_api == "DeepSeek":
                        if "data" in result and "content" in result["data"]:
                            content = result["data"]["content"]
                            self.messages.append({
                                "role": "assistant",
                                "content": content
                            })
                            return content
                    elif self.current_api == "Ultra":
                        if result["code"] == 200 and "choices" in result:
                            content = result["choices"][0]["message"]["content"]
                            if "sessionid" in result and result["sessionid"]:
                                self.ultra_config["sessionid"] = result["sessionid"]
                            self.messages.append({
                                "role": "assistant",
                                "content": content,
                                "model": result.get("model", "4.0Ultra")
                            })
                            return content
                    elif self.current_api == "Max":
                        if result["code"] == 200:
                            if result.get("answer"):
                                content = result["answer"]
                                self.messages.append({
                                    "role": "assistant",
                                    "content": content
                                })
                                return content
                            else:
                                return "AI 暂时无法回复"
                        else:
                            return "AI 暂时无法回复"
                    elif self.current_api == "Moonshot":
                        if result["code"] == 200:
                            if result.get("msg"):
                                content = result["msg"]
                                self.messages.append({
                                    "role": "assistant",
                                    "content": content
                                })
                                return content
                            else:
                                return "AI 暂时无法回复"
                        else:
                            return "AI 暂时无法回复"
                    else:
                        if "choices" in result and len(result["choices"]) > 0:
                            content = result["choices"][0]["message"]["content"]
                            self.messages.append({
                                "role": "assistant",
                                "content": content
                            })
                            return content
                    
                    return "无法获取 AI 响应"
                
            except requests.exceptions.RequestException as e:
                error_msg = f"API请求错误: {str(e)}"
                self.logger.error(error_msg)
                
                # 尝试切换到备用模型
                success, msg = self.switch_to_fallback(current_model, error_msg)
                if success:
                    self.logger.info(msg)
                    print(f"\n{msg}")
                    retries += 1
                    continue
                else:
                    self.logger.error(msg)
                    return f"发送消息失败: {error_msg}"
                
            except Exception as e:
                error_msg = f"发生错误: {str(e)}"
                self.logger.error(error_msg)
                
                # 尝试切换到备用模型
                success, msg = self.switch_to_fallback(current_model, error_msg)
                if success:
                    self.logger.info(msg)
                    print(f"\n{msg}")
                    retries += 1
                    continue
                else:
                    self.logger.error(msg)
                    return f"发送消息失败: {error_msg}"
        
        return "所有重试都失败了，请稍后再试"

class LoadingAnimation:
    def __init__(self, desc="思考中"):
        self.desc = desc
        self.done = False
        self.spinner = cycle(['◜', '◠', '◝', '◞', '◡', '◟'])
    
    def animate(self):
        while not self.done:
            sys.stdout.write(f'\r{self.desc} {next(self.spinner)} ')
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\r' + ' ' * 50 + '\r')
        sys.stdout.flush()
    
    def start(self):
        self.thread = threading.Thread(target=self.animate)
        self.thread.start()
    
    def stop(self):
        self.done = True
        if hasattr(self, 'thread'):
            self.thread.join()

def setup_logger():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    log_filename = f"logs/aichat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    if logger.handlers:
        logger.handlers.clear()
    
    # 只保留文件处理器，移除控制台处理器
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)
    
    # 只添加文件处理器
    logger.addHandler(file_handler)
    
    return logger

def print_welcome_banner():
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                      江江 AI 聊天助手                         ║
║                JiangYiuの自留地💤: 1028010826                ║  
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """命令行版本的主函数"""
    print_welcome_banner()
    chat = AIChat()
    print(f"\n✨ 当前使用模型: {chat.model}")
    print("\n📝 功能菜单:")
    print("  • 输入 'qc'     - 退出程序")
    print("  • 输入 'qh'     - 切换AI模型")
    print("  • 输入 'sd'     - 设置默认模型")
    print("  • 输入 'config' - 配置当前模型")
    print("\n" + "═" * 60)
    
    while True:
        user_input = input("\n你: ").strip()
        
        if user_input.lower() == 'qc':
            print("再见！")
            break
            
        if user_input.lower() == 'qh':
            chat.change_model()
            continue
            
        if user_input.lower() == 'sd':
            chat.set_default_model()
            continue
            
        if user_input.lower() == 'config':
            if chat.model == "DeepSeekPro":
                chat.configure_deepseek_pro()
            elif chat.model == "Ultra":
                chat.configure_ultra()
            continue
            
        if not user_input:
            continue
        
        loading = LoadingAnimation(f"AI思考中 ({chat.model})")
        loading.start()
        
        response = chat.send_message(user_input)
        
        loading.stop()
        
        print(f"\nAI ({chat.model}):", response)

# 如果是直接运行此文件，执行命令行版本
if __name__ == "__main__":
    main() 