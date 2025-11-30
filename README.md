<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Vue.js-3.4-green.svg" alt="Vue.js">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-teal.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/AI-GPT--4o-purple.svg" alt="AI Powered">
</p>

<h1 align="center">MD Audit</h1>

<p align="center">
  <strong>Intelligent Markdown SEO Diagnostic Agent</strong><br>
  Dual-engine analysis combining rule-based checking with AI semantic analysis
</p>

<p align="center">
  <a href="#features">Features</a> |
  <a href="#quick-start">Quick Start</a> |
  <a href="#docker">Docker</a> |
  <a href="#cli-usage">CLI</a> |
  <a href="#api-reference">API</a> |
  <a href="./README_CN.md">中文文档</a>
</p>

---

## Overview

**MD Audit** is a Python-based SEO diagnostic agent for Markdown content. It combines a rule-based engine (75% weight) with AI semantic analysis (25% weight) to evaluate SEO quality and provide actionable optimization suggestions.

**Key Benefits:**
- **Native Markdown Support** - Analyze `.md` files directly
- **Dual-Engine Analysis** - Fast rules + intelligent AI insights
- **Beautiful Web UI** - Vue.js interface with Aurora animations
- **Actionable Reports** - Specific suggestions with code examples
- **Graceful Degradation** - Falls back to rule-only when AI unavailable

---

## Quick Start

### One-Command Setup

```bash
# Clone and install
git clone https://github.com/JasonRobertDestiny/MD_Audit.git
cd MD_Audit
make install

# Set API key (optional, for AI analysis)
export MD_AUDIT_LLM_API_KEY=your_openai_api_key

# Start the application
make serve
```

Access at **http://localhost:8000**

### Development Mode

```bash
# Frontend hot-reload + backend auto-reload
make dev
```
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

---

## Docker

### Quick Run

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

## Features

### Scoring Dimensions

| Dimension | Weight | Checks |
|-----------|--------|--------|
| **Metadata** | 30% | Title (30-60 chars), Description (120-160 chars) |
| **Structure** | 25% | Unique H1, Image alt coverage (>=80%), Links |
| **Keywords** | 20% | Density (1%-2.5%), Placement in title/desc/first paragraph |
| **AI Semantic** | 25% | Content depth, Readability, Topic relevance |

### Score Grades

| Score | Grade | Action |
|-------|-------|--------|
| 90-100 | Excellent | Publish ready |
| 70-89 | Good | Minor tweaks |
| 50-69 | Needs Work | Review suggestions |
| 0-49 | Poor | Major revision needed |

---

## CLI Usage

```bash
# Basic analysis
python -m md_audit.main analyze article.md

# With keywords
python -m md_audit.main analyze article.md -k "Python" "SEO"

# Save report
python -m md_audit.main analyze article.md -o report.md

# Disable AI (rules only, faster)
python -m md_audit.main analyze article.md --no-ai

# Batch directory analysis
python -m md_audit.main analyze docs/ -o reports/ --workers 8
```

---

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Analyze Markdown file |
| `POST` | `/api/analyze/batch` | Batch analysis |
| `GET` | `/api/history` | Analysis history |
| `GET` | `/api/health` | Health check |
| `GET` | `/docs` | Swagger UI |

### Example

```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -F "file=@article.md" \
  -F "keywords=SEO,Markdown"
```

Response:
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

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MD_AUDIT_LLM_API_KEY` | OpenAI API key | - |
| `MD_AUDIT_LLM_MODEL` | Model name | `gpt-4o` |
| `MD_AUDIT_LLM_BASE_URL` | API base URL | OpenAI default |
| `SEO_RULES_CONFIG` | Config file path | `config/default_config.json` |

### Config File

`config/default_config.json`:

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

## Architecture

```
MD_Audit/
├── md_audit/              # Core Python package
│   ├── main.py            # CLI entry
│   ├── analyzer.py        # Analysis orchestrator
│   ├── engines/
│   │   ├── rules_engine.py    # Rule-based checks
│   │   └── ai_engine.py       # AI semantic analysis
│   ├── parsers/
│   │   └── markdown_parser.py # Frontmatter + MD parsing
│   └── models/
│       └── data_models.py     # Pydantic models
├── frontend/              # Vue.js web UI
├── web/                   # FastAPI backend
├── config/                # Configuration
└── tests/                 # Test suite
```

---

## Development

```bash
# Run tests
make test

# Format code
black md_audit/

# Lint
ruff check md_audit/

# Build frontend only
make build
```

---

## Tech Stack

**Backend:** Python 3.8+, FastAPI, Pydantic, OpenAI, BeautifulSoup4

**Frontend:** Vue.js 3.4, Tailwind CSS, Vite, Axios

---

## License

MIT License - see [LICENSE](LICENSE)

---

<p align="center">
  <a href="https://github.com/JasonRobertDestiny">@JasonRobertDestiny</a>
</p>
