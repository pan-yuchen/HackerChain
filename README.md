# 🔗 HackerChain

一个基于AI的智能对话分析与内容生成系统，专为创业者和黑客马拉松参与者设计，能够分析对话内容并生成创业方案、HTML页面和小红书营销内容。

## ✨ 主要功能

### 🤖 智能对话分析
- **实时AI对话**：基于DeepSeek模型的智能对话系统
- **对话历史管理**：自动保存和恢复对话记录
- **多轮对话支持**：支持上下文相关的连续对话

### 📊 创业内容生成
- **需求提取**：从对话中智能提取创业需求和关键信息
- **方案生成**：自动生成创业方案和解决步骤
- **可视化建议**：提供数据可视化和展示建议

### 🎨 多媒体内容创作
- **HTML页面生成**：根据分析结果自动生成现代化网页
- **海报设计**：AI驱动的宣传海报自动生成
- **小红书内容**：智能生成适合社交媒体的营销文案

### 📱 小红书集成
- **MCP客户端**：通过MCP协议连接小红书服务
- **内容发布**：支持图文和视频内容发布
- **互动功能**：点赞、收藏、评论等社交功能

## 🏗️ 系统架构

```
├── 前端界面 (HTML/CSS/JavaScript)
│   ├── 对话区域
│   ├── 结果展示
│   └── 功能控制面板
│
├── 后端服务 (Flask)
│   ├── AI模型集成 (DeepSeek)
│   ├── 对话分析引擎
│   ├── 内容生成器
│   └── 小红书MCP客户端
│
└── 外部服务
    ├── DeepSeek API
    ├── OpenRouter (图像生成)
    └── 小红书MCP服务器
```

## 🛠️ 技术栈

### 后端
- **Python 3.8+**
- **Flask** - Web框架
- **OpenAI SDK** - AI模型接口
- **Requests** - HTTP客户端
- **Flask-CORS** - 跨域支持

### 前端
- **HTML5/CSS3/JavaScript**
- **响应式设计**
- **模态窗口**
- **实时状态管理**

### AI服务
- **DeepSeek Reasoner** - 对话分析
- **DeepSeek Chat** - 实时聊天
- **Gemini 2.5 Flash** - 图像生成

## 📦 安装说明

### 1. 克隆项目

```bash
git clone https://github.com/pan-yuchen/HackerChain.git
cd HackerChain
```

### 2. 创建虚拟环境（推荐）

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install flask flask-cors openai requests pillow
```

### 4. 环境配置

创建 `.env` 文件或直接在代码中配置以下环境变量：

```env
# DeepSeek API配置
OPENAI_API_KEY=your_deepseek_api_key
OPENAI_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-reasoner

# OpenRouter API配置（用于图像生成）
OPENROUTER_API_KEY=your_openrouter_api_key

# Flask配置
FLASK_DEBUG=True
FLASK_PORT=5001
```

### 5. 创建必要的目录

```bash
mkdir -p analysis_outputs generated_html output
```

### 6. 启动服务

```bash
python main_deepssek.py
```

访问 `http://localhost:5001` 开始使用系统。

## 🚀 快速开始

### 基本使用流程

1. **开始对话**
   - 在对话区域输入你的创业想法或问题
   - AI助手会实时回复并提供建议

2. **分析对话**
   - 点击"📊 总结对话内容"按钮
   - 系统会分析对话并提取关键信息

3. **生成内容**
   - **HTML页面**：点击"🎨 生成HTML"创建项目展示页面
   - **宣传海报**：点击"🎯 生成宣传海报"设计营销素材
   - **小红书内容**：点击"📱 发表小红书"生成社交媒体文案

### 示例对话

```
用户：我想做一个AI健身助手的创业项目
助手：这是一个很有前景的想法！AI健身助手可以提供个性化训练计划...

用户：具体应该包含哪些功能？
助手：建议包含以下核心功能：
      1. 动作识别与纠正
      2. 个性化训练计划
      3. 实时反馈系统
      ...
```

## 📁 项目结构

```
HackerChain/
├── main_deepssek.py          # 主应用服务器
├── mcp.py                    # 小红书MCP客户端
├── poster_designer.py        # 海报设计模块
├── templates/
│   └── inner_index.html      # 前端界面
├── analysis_outputs/         # 分析结果存储（自动创建）
├── generated_html/           # 生成的HTML文件（自动创建）
├── output/                   # 生成的图片文件（自动创建）
├── .env                      # 环境配置文件（需创建）
└── README.md                 # 项目文档
```

## 🔧 核心模块说明

### 1. AI对话引擎 (`main_deepssek.py`)
- **DeepSeekReasoner**：用于复杂分析和推理
- **DeepSeekChat**：用于实时对话交互
- **对话分析器**：提取创业需求和关键信息
- **Flask API**：提供REST接口服务

### 2. 小红书客户端 (`mcp.py`)
- **XiaohongshuMCPClient**：MCP协议客户端
- **内容发布**：支持图文和视频发布
- **社交互动**：点赞、收藏、评论功能

### 3. 海报设计器 (`poster_designer.py`)
- **品牌生成**：基于创意生成品牌包装
- **图像生成**：调用AI模型生成海报
- **样式定制**：支持颜色、布局等定制

## 🎯 使用场景

### 创业者
- **项目验证**：通过AI对话验证创业想法
- **方案制定**：生成详细的实施方案
- **营销准备**：创建宣传材料和社交媒体内容

### 黑客马拉松参与者
- **快速原型**：48小时内生成项目展示页面
- **团队协作**：通过对话整理项目思路
- **演示准备**：生成专业的展示材料

### 产品经理
- **需求分析**：通过对话梳理产品需求
- **方案设计**：生成产品设计方案
- **市场推广**：创建营销内容和宣传材料

## 🔐 API配置

### DeepSeek API

1. 访问 [DeepSeek Platform](https://platform.deepseek.com/) 注册账号
2. 在控制台获取API密钥
3. 在 `.env` 文件或代码中配置 `OPENAI_API_KEY`

```python
# 在 main_deepssek.py 中配置
API_KEY = "your_deepseek_api_key"
```

### OpenRouter API (海报生成)

1. 访问 [OpenRouter](https://openrouter.ai/) 注册账号
2. 获取API密钥
3. 在 `poster_designer.py` 中配置密钥

```python
# 在 poster_designer.py 中配置
OPENROUTER_API_KEY = "your_openrouter_api_key"
```

## ⚠️ 注意事项

1. **API密钥安全**：请不要将API密钥提交到公开仓库
2. **端口冲突**：如果5001端口被占用，可在 `main_deepssek.py` 中修改端口
3. **依赖版本**：确保Python版本 >= 3.8
4. **网络连接**：需要稳定的网络连接访问AI服务

## 🐛 常见问题

### Q: 启动时提示端口被占用？
A: 修改 `main_deepssek.py` 中的 `app.run(port=5001)` 为其他端口

### Q: API调用失败？
A: 检查API密钥是否正确配置，网络是否可以访问API服务

### Q: 生成的文件在哪里？
A: 
- HTML文件：`generated_html/` 目录
- 分析结果：`analysis_outputs/` 目录
- 图片文件：`output/` 目录

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置

1. Fork项目到你的GitHub账号
2. 创建新的功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 创建Pull Request

### 代码规范

- 使用Python PEP 8代码风格
- 添加适当的注释和文档字符串
- 确保所有功能都有相应的错误处理
- 测试新功能后再提交

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👥 作者

- **pan-yuchen** - [GitHub](https://github.com/pan-yuchen)

## 🙏 致谢

- DeepSeek 提供强大的AI模型支持
- OpenRouter 提供图像生成服务
- 所有贡献者的支持和反馈

---

⭐ 如果这个项目对你有帮助，请给它一个星标！

📧 有问题或建议？欢迎提交 [Issue](https://github.com/pan-yuchen/HackerChain/issues)
