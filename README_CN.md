<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Vue.js-3.4-green.svg" alt="Vue.js">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-teal.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/AI-GPT--4o-purple.svg" alt="AI Powered">
</p>

<h1 align="center">MD Audit</h1>

<p align="center">
  <strong>智能 Markdown SEO 诊断 Agent</strong><br>
  结合规则引擎与 AI 语义分析的双引擎诊断系统
</p>

<p align="center">
  <a href="#核心特性">特性</a> |
  <a href="#快速开始">快速开始</a> |
  <a href="#docker-部署">Docker</a> |
  <a href="#命令行使用">CLI</a> |
  <a href="#api-接口">API</a> |
  <a href="./README.md">English</a>
</p>

---

## 项目简介

**MD Audit** 是基于 Python 的 Markdown SEO 诊断 Agent。采用双引擎架构：规则引擎（75% 权重）+ AI 语义分析（25% 权重），自动评估内容质量并提供可执行的优化建议。

**核心优势：**
- **原生 Markdown 支持** - 直接分析 `.md` 文件，无需转换
- **双引擎分析** - 快速规则检查 + 智能 AI 洞察
- **精美 Web 界面** - Vue.js 界面，配备 Aurora 动画效果
- **可执行建议** - 提供具体的代码示例，而非泛泛而谈
- **优雅降级** - AI 不可用时自动切换为纯规则分析

---

## 快速开始

### 一键启动

```bash
# 克隆并安装
git clone https://github.com/JasonRobertDestiny/MD_Audit.git
cd MD_Audit
make install

# 设置 API 密钥（可选，用于 AI 分析）
export MD_AUDIT_LLM_API_KEY=your_openai_api_key

# 启动应用
make serve
```

访问 **http://localhost:8000**

### 开发模式

```bash
# 前端热更新 + 后端自动重载
make dev
```
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000

---

## Docker 部署

### 快速运行

```bash
docker build -t md-audit .
docker run -p 8000:8000 -e MD_AUDIT_LLM_API_KEY=your_key md-audit
```

### Docker Compose

```yaml
version: '3.8'
services:
  md-audit:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MD_AUDIT_LLM_API_KEY=${MD_AUDIT_LLM_API_KEY}
    volumes:
      - ./data:/app/data
```

```bash
docker-compose up -d
```

---

## 核心特性

### 评分维度

| 维度 | 权重 | 检查项 |
|------|------|--------|
| **元数据** | 30% | Title（30-60字符）、Description（120-160字符） |
| **结构** | 25% | H1 唯一性、图片 Alt 覆盖率（>=80%）、链接 |
| **关键词** | 20% | 密度（1%-2.5%）、在标题/描述/首段的位置 |
| **AI 语义** | 25% | 内容深度、可读性、主题相关性 |

### 分数等级

| 分数 | 等级 | 建议操作 |
|------|------|----------|
| 90-100 | 优秀 | 可直接发布 |
| 70-89 | 良好 | 稍作调整 |
| 50-69 | 需改进 | 查看建议 |
| 0-49 | 较差 | 需大幅修改 |

---

## 命令行使用

```bash
# 基础分析
python -m md_audit.main analyze article.md

# 指定关键词
python -m md_audit.main analyze article.md -k "Python" "SEO"

# 保存报告
python -m md_audit.main analyze article.md -o report.md

# 禁用 AI（仅规则检查，更快）
python -m md_audit.main analyze article.md --no-ai

# 批量分析目录
python -m md_audit.main analyze docs/ -o reports/ --workers 8
```

---

## API 接口

### 端点列表

| 方法 | 端点 | 描述 |
|------|------|------|
| `POST` | `/api/analyze` | 分析 Markdown 文件 |
| `POST` | `/api/analyze/batch` | 批量分析 |
| `GET` | `/api/history` | 分析历史 |
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/docs` | Swagger 文档 |

### 请求示例

```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -F "file=@article.md" \
  -F "keywords=SEO,Markdown"
```

响应：
```json
{
  "total_score": 85.5,
  "metadata_score": 28.0,
  "structure_score": 22.5,
  "keyword_score": 18.0,
  "ai_score": 17.0,
  "diagnostics": [...],
  "suggestions": [...],
  "extracted_keywords": ["python", "seo", "markdown"]
}
```

---

## 配置说明

### 环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `MD_AUDIT_LLM_API_KEY` | OpenAI API 密钥 | - |
| `MD_AUDIT_LLM_MODEL` | 模型名称 | `gpt-4o` |
| `MD_AUDIT_LLM_BASE_URL` | API 基础地址 | OpenAI 默认 |
| `SEO_RULES_CONFIG` | 配置文件路径 | `config/default_config.json` |

### 配置文件

`config/default_config.json`：

```json
{
  "title_rules": { "min_length": 30, "max_length": 60 },
  "description_rules": { "min_length": 120, "max_length": 160 },
  "keyword_rules": { "min_density": 0.01, "max_density": 0.025 },
  "content_rules": { "min_length": 300, "min_image_alt_ratio": 0.8 },
  "enable_ai_analysis": true
}
```

---

## 项目架构

```
MD_Audit/
├── md_audit/              # 核心 Python 包
│   ├── main.py            # CLI 入口
│   ├── analyzer.py        # 分析协调器
│   ├── engines/
│   │   ├── rules_engine.py    # 规则引擎
│   │   └── ai_engine.py       # AI 语义分析
│   ├── parsers/
│   │   └── markdown_parser.py # Frontmatter + MD 解析
│   └── models/
│       └── data_models.py     # Pydantic 模型
├── frontend/              # Vue.js Web 界面
├── web/                   # FastAPI 后端
├── config/                # 配置文件
└── tests/                 # 测试套件
```

---

## 开发指南

```bash
# 运行测试
make test

# 格式化代码
black md_audit/

# 代码检查
ruff check md_audit/

# 仅构建前端
make build
```

---

## 技术栈

**后端：** Python 3.8+、FastAPI、Pydantic、OpenAI、BeautifulSoup4

**前端：** Vue.js 3.4、Tailwind CSS、Vite、Axios

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

<p align="center">
  <a href="https://github.com/JasonRobertDestiny">@JasonRobertDestiny</a>
</p>
