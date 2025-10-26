from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from datetime import datetime
import json
import os
import traceback
import logging
import base64
from typing import List, Dict, Any
from mcp import XiaohongshuMCPClient
from poster_designer import design

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ===== 配置管理 =====
class Config:
    def __init__(self):
        # 从环境变量获取配置，如果没有则使用默认值
        self.api_key = os.getenv('OPENAI_API_KEY', 'sk-6bbcc10fdd71459d9c64a19b49a1bf8d')
        self.base_url = os.getenv('OPENAI_BASE_URL', 'https://api.deepseek.com/v1')
        self.deepseek_model = os.getenv('DEEPSEEK_MODEL', 'deepseek-reasoner')
        self.flask_debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
        self.flask_port = int(os.getenv('FLASK_PORT', '5001'))

config = Config()

# ===== 模型定义 =====
    
class DeepSeekReasoner:
    def __init__(self):
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )

    def __call__(self, messages) -> str:
        try:
            if isinstance(messages, str):
                formatted_messages = [{'role': 'user', 'content': messages}]
            elif isinstance(messages, list):
                formatted_messages = []
                for msg in messages:
                    if isinstance(msg, dict):
                        formatted_messages.append(msg)
                    elif hasattr(msg, 'content'):
                        role = 'user'
                        if hasattr(msg, 'type'):
                            role = 'user' if msg.type == 'human' else 'assistant'
                        formatted_messages.append({
                            'role': role,
                            'content': msg.content
                        })
            else:
                formatted_messages = [{'role': 'user', 'content': str(messages)}]

            response = self.client.chat.completions.create(
                model='deepseek-reasoner',  # 恢复使用reasoner模型
                messages=formatted_messages,
                max_tokens=8192,            # 恢复更大的token限制
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"DeepSeek API Error: {e}")
            raise e

    
class DeepSeekChat:
    def __init__(self):
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )

    def __call__(self, messages) -> str:
        try:
            if isinstance(messages, str):
                formatted_messages = [{'role': 'user', 'content': messages}]
            elif isinstance(messages, list):
                formatted_messages = []
                for msg in messages:
                    if isinstance(msg, dict):
                        formatted_messages.append(msg)
                    elif hasattr(msg, 'content'):
                        role = 'user'
                        if hasattr(msg, 'type'):
                            role = 'user' if msg.type == 'human' else 'assistant'
                        formatted_messages.append({
                            'role': role,
                            'content': msg.content
                        })
            else:
                formatted_messages = [{'role': 'user', 'content': str(messages)}]

            response = self.client.chat.completions.create(
                model='deepseek-chat',
                messages=formatted_messages,
                max_tokens=8192,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"DeepSeek API Error: {e}")
            raise e


# ===== 辅助函数 =====
def clean_json_response(response: str) -> str:
    """清理响应中的markdown标记"""
    cleaned = response.replace('```json', '').replace('```', '').strip()
    start = cleaned.find('{')
    end = cleaned.rfind('}') + 1
    if start >= 0 and end > start:
        cleaned = cleaned[start:end]
    return cleaned


def clean_html_response(response: str) -> str:
    """清理响应中的HTML markdown标记"""
    cleaned = response.replace('```html', '').replace('```', '').strip()
    return cleaned


def render_html(html_content: str, filename: str = None) -> str:
    """保存HTML内容到文件"""
    output_dir = "generated_html"
    os.makedirs(output_dir, exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"visualization_{timestamp}.html"

    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"HTML已保存到: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"保存HTML文件失败: {e}")
        raise


def analyze_dialog(dialog_text: str) -> Dict[str, Any]:
    """分析对话内容"""

    prompt = f"""你是一位商业、创业和黑客马拉松专家，给你一位想要创业或者参加黑客马拉松的用户和大模型的对话历史，你要做的就是仔细研读用户的对话，然后针对该用户需求，生成以下内容：

1. 生成用于文生图的prompt
2. 生成用于制作该主题HTML页面的prompt
3. 生成用于该主题宣传发在小红书的文案

务必仅仅返回标准json格式的结果，包含以下字段：
{{
    "image_prompt": "详细的文生图prompt，描述要生成的图片内容、风格、色彩等",
    "html_prompt": "详细的HTML制作prompt，描述页面结构、样式、交互等要求",
    "xiaohongshu_title": "小红书标题",
    "xiaohongshu_content": "完整的小红书文案，包含标题和正文内容，适合该主题的宣传推广"
}}

【对话历史】
{dialog_text}

请直接输出JSON对象："""

    try:
        response = reasoner_model(prompt)
        cleaned_response = clean_json_response(response)
        result_dict = json.loads(cleaned_response)

        # 确保必要字段存在
        default_fields = {
            'image_prompt': '',
            'html_prompt': '',
            'xiaohongshu_title': '',
            'xiaohongshu_content': ''
        }
        
        for field, default_value in default_fields.items():
            if field not in result_dict:
                result_dict[field] = default_value

        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "analysis_outputs"
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f"analysis_{timestamp}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"分析结果已保存到: {output_path}")
        return result_dict

    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {e}")
        return {
            "error": "JSON解析失败",
            "image_prompt": "",
            "html_prompt": "",
            "xiaohongshu_title": "",
            "xiaohongshu_content": ""
        }
    except Exception as e:
        logger.error(f"分析出错: {str(e)}")
        traceback.print_exc()
        return {
            "error": f"分析失败: {str(e)}",
            "image_prompt": "",
            "html_prompt": "",
            "xiaohongshu_title": "",
            "xiaohongshu_content": ""
        }


def generate_html_from_analysis(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """根据分析结果生成HTML"""

    html_generate_prompt = f"""
任务：你是一个专业的前端开发者，你需要根据以下分析结果制作一个现代化、美观的HTML页面。

分析结果如下：
{json.dumps(analysis_result, ensure_ascii=False, indent=2)}

输出要求：仅输出完整可运行的HTML代码，不需要任何解释或额外文本。请直接输出HTML，不要添加任何前缀、后缀或解释文字，不要使用```html或任何代码块标记。
"""

    try:
        response = reasoner_model(html_generate_prompt)
        cleaned_html = clean_html_response(response)

        if not cleaned_html.startswith('<!DOCTYPE'):
            cleaned_html = '<!DOCTYPE html>\n' + cleaned_html

        # 保存HTML
        filepath = render_html(cleaned_html)

        return {
            'success': True,
            'filepath': filepath,
            'html': cleaned_html
        }
    except Exception as e:
        logger.error(f"生成HTML出错: {str(e)}")
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


# 存储最新的分析结果
latest_analysis = None

# 初始化模型
chat_model = DeepSeekChat()      # 用于聊天的快速模型
reasoner_model = DeepSeekReasoner()  # 用于分析的推理模型

# 初始化小红书MCP客户端（延迟初始化）
xiaohongshu_client = None


@app.route('/')
def index():
    """主页路由"""
    try:
        return render_template('inner_index.html')
    except Exception as e:
        logger.error(f"渲染主页失败: {e}")
        return jsonify({'error': '页面加载失败'}), 500


@app.route('/chat', methods=['POST'])
def chat():
    """聊天接口"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        user_message = data.get('message', '')
        dialog_history = data.get('dialog_history', [])

        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400

        logger.info(f"收到用户消息: {user_message[:100]}...")
        
        # 构建完整的对话历史，包括当前消息
        messages = []
        for item in dialog_history:
            if item.get('role') == 'user':
                messages.append({"role": "user", "content": item.get('content', '')})
            elif item.get('role') == 'assistant':
                messages.append({"role": "assistant", "content": item.get('content', '')})
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        # 如果没有历史对话，直接传递单条消息
        if len(messages) == 1:
            response = chat_model(user_message)
        else:
            response = chat_model(messages)

        return jsonify({
            'response': response,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })

    except Exception as e:
        logger.error(f"Chat error: {e}")
        traceback.print_exc()
        return jsonify({'error': f'聊天服务出错: {str(e)}'}), 500


@app.route('/extract', methods=['POST'])
def extract_requirements():
    """处理需求提取请求"""
    global latest_analysis

    try:
        data = request.json
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        dialog_history = data.get('dialog', [])

        if not dialog_history:
            return jsonify({'error': '对话历史为空'}), 400

        # 将对话历史格式化为文本
        dialog_text = ""
        for msg in dialog_history:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                continue
            role = "用户" if msg['role'] == 'user' else "助手"
            dialog_text += f"{role}: {msg['content']}\n\n"

        logger.info(f"开始分析对话，长度: {len(dialog_text)}")

        # 分析对话
        analysis_result = analyze_dialog(dialog_text)

        # 保存最新的分析结果
        latest_analysis = analysis_result

        # 检查是否有错误
        if 'error' in analysis_result and analysis_result['error'] and not any([
            analysis_result.get('knowledge_points'),
            analysis_result.get('solution_steps'),
            analysis_result.get('image_prompt'),
            analysis_result.get('html_prompt'),
            analysis_result.get('xiaohongshu_title'),
            analysis_result.get('xiaohongshu_content')
        ]):
            return jsonify({'error': analysis_result['error']}), 500

        return jsonify({
            'status': 'success',
            'analysis': analysis_result,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        logger.error(f"Extract error: {e}")
        traceback.print_exc()
        return jsonify({'error': f'需求提取失败: {str(e)}'}), 500


@app.route('/generate_html', methods=['POST'])
def generate_html():
    """生成HTML可视化"""
    global latest_analysis

    try:
        data = request.json
        if not data:
            data = {}

        # 可以传入分析结果，或使用最新的分析结果
        analysis = data.get('analysis')

        if not analysis:
            if latest_analysis:
                analysis = latest_analysis
            else:
                dialog_history = data.get('dialog', [])
                if not dialog_history:
                    return jsonify({'error': '需要先进行需求分析或提供对话历史'}), 400

                dialog_text = ""
                for msg in dialog_history:
                    if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                        continue
                    role = "用户" if msg['role'] == 'user' else "助手"
                    dialog_text += f"{role}: {msg['content']}\n\n"

                analysis = analyze_dialog(dialog_text)
                latest_analysis = analysis

        logger.info("开始生成HTML页面")

        # 生成HTML
        result = generate_html_from_analysis(analysis)

        if result['success']:
            # 返回完整的HTML内容
            return jsonify({
                'status': 'success',
                'html_content': result['html'],
                'filename': os.path.basename(result['filepath'])
            })
        else:
            return jsonify({'error': result['error']}), 500

    except Exception as e:
        logger.error(f"Generate HTML error: {e}")
        traceback.print_exc()
        return jsonify({'error': f'HTML生成失败: {str(e)}'}), 500


@app.route('/publish_xiaohongshu', methods=['POST'])
def publish_xiaohongshu():
    """发布内容到小红书"""
    global latest_analysis, xiaohongshu_client

    try:
        data = request.json
        if not data:
            return jsonify({'error': '请求数据为空'}), 400

        # 获取发布参数
        title = data.get('title', '')
        content = data.get('content', '')
        images = data.get('images', [])
        tags = data.get('tags', [])

        # 参数验证
        if not title:
            return jsonify({'error': '标题不能为空'}), 400
        if not content:
            return jsonify({'error': '内容不能为空'}), 400
        
        # 图片是可选的，如果没有提供则设为空列表
        if not images:
            images = []

        # 检查标题长度（最多20个中文字）
        if len(title) > 20:
            return jsonify({'error': '标题不能超过20个字符'}), 400

        logger.info(f"开始发布小红书内容，标题: {title}")

        # 初始化MCP客户端连接（如果还没有初始化）
        if xiaohongshu_client is None:
            xiaohongshu_client = XiaohongshuMCPClient()
        
        # 确保客户端已初始化
        if not xiaohongshu_client.initialized:
            try:
                init_result = xiaohongshu_client.initialize()
                logger.info(f"MCP客户端初始化成功: {init_result}")
            except Exception as e:
                logger.error(f"MCP客户端初始化失败: {e}")
                return jsonify({'error': f'MCP客户端初始化失败: {str(e)}'}), 500

        # 调用发布方法
        result = xiaohongshu_client.publish_content(
            title=title,
            content=content,
            images=images,
            tags=tags if tags else None
        )

        logger.info(f"发布结果: {result}")

        # 检查发布结果
        if 'result' in result:
            result_content = result['result']
            if 'content' in result_content:
                content_list = result_content['content']
                for content_item in content_list:
                    if content_item.get('type') == 'text':
                        response_text = content_item.get('text', '')
                        logger.info(f"服务器响应: {response_text}")
                        
            return jsonify({
                'status': 'success',
                'message': '发布成功！',
                'result': result['result']
            })
        elif 'error' in result:
            error_info = result['error']
            error_message = error_info.get('message', '未知错误') if isinstance(error_info, dict) else str(error_info)
            logger.error(f"发布失败: {error_message}")
            return jsonify({
                'status': 'error',
                'error': f"发布失败: {error_message}"
            }), 500
        else:
            return jsonify({
                'status': 'success',
                'message': '发布请求已提交',
                'result': result
            })

    except Exception as e:
        logger.error(f"发布小红书内容出错: {e}")
        traceback.print_exc()
        return jsonify({'error': f'发布失败: {str(e)}'}), 500


@app.route('/generate_poster', methods=['POST'])
def generate_poster():
    """生成海报"""
    global latest_analysis

    try:
        data = request.json
        if not data:
            data = {}

        # 可以传入分析结果，或使用最新的分析结果
        analysis = data.get('analysis')

        if not analysis:
            if latest_analysis:
                analysis = latest_analysis
            else:
                return jsonify({'error': '需要先进行需求分析'}), 400

        # 获取image_prompt
        image_prompt = analysis.get('image_prompt', '')
        if not image_prompt:
            return jsonify({'error': '分析结果中没有找到image_prompt'}), 400

        logger.info("开始生成海报")

        # 调用poster_designer的design函数
        output_dir = "output"
        design(idea="", output_dir=output_dir, image_prompt=image_prompt)

        # 检查生成的图片文件
        generated_files = []
        image_data = []
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                if file.startswith('generated_image_') and file.endswith(('.png', '.jpg', '.jpeg')):
                    generated_files.append(file)
                    # 读取图片文件并转换为base64
                    file_path = os.path.join(output_dir, file)
                    try:
                        with open(file_path, 'rb') as img_file:
                            img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                            image_data.append({
                                'filename': file,
                                'base64': img_base64,
                                'path': file_path
                            })
                    except Exception as e:
                        logger.error(f"读取图片文件失败 {file}: {e}")

        if generated_files:
            return jsonify({
                'status': 'success',
                'message': '海报生成成功！',
                'generated_files': generated_files,
                'output_dir': output_dir,
                'images': image_data
            })
        else:
            return jsonify({'error': '海报生成失败，未找到生成的图片文件'}), 500

    except Exception as e:
        logger.error(f"Generate poster error: {e}")
        traceback.print_exc()
        return jsonify({'error': f'海报生成失败: {str(e)}'}), 500


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({'error': '页面未找到'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': '服务器内部错误'}), 500


if __name__ == '__main__':
    logger.info(f"启动Flask应用，端口: {config.flask_port}, 调试模式: {config.flask_debug}")
    app.run(debug=config.flask_debug, port=config.flask_port, host='0.0.0.0')