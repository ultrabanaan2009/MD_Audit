"""
MD Audit 配置系统 - 2025 SEO Standards
基于 Ahrefs, SEMrush, Backlinko 权威标准
"""
import os
import json
from dataclasses import dataclass, asdict, field
from typing import Optional, List
from pathlib import Path

# 自动加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class TitleRules:
    """
    标题规则配置 - 2025 Standard
    Source: Ahrefs, Search Engine Land
    - 50-60 chars optimal (600px max on desktop SERP)
    - Front-load keywords
    """
    min_length: int = 50
    max_length: int = 60
    optimal_pixels: int = 600
    weight: float = 15.0


@dataclass
class DescriptionRules:
    """
    描述规则配置 - 2025 Standard
    Source: SEMrush, Stan Ventures
    - Desktop: 150-160 chars (920px max)
    - Mobile: ~120 chars (680px max)
    """
    min_length: int = 150
    max_length: int = 160
    mobile_max_length: int = 120
    optimal_pixels: int = 920
    weight: float = 10.0


@dataclass
class KeywordRules:
    """
    关键词规则配置 - 2025 Standard
    - Natural usage over density (keyword stuffing penalized)
    - Semantic/LSI keywords more important than exact match
    """
    min_density: float = 0.005
    max_density: float = 0.02
    max_auto_keywords: int = 5
    weight: float = 15.0


@dataclass
class ContentRules:
    """
    内容规则配置 - 2025 Standard
    Source: Backlinko (avg top 10 = 1,447 words), Wix Blog (2,450 optimal)
    - Minimum 1,500 words for comprehensive coverage
    - Optimal 2,000-2,500 words
    - Alt text: 80-125 chars for accessibility
    """
    min_length: int = 1500
    optimal_length: int = 2000
    max_length: int = 3500
    min_h1_count: int = 1
    max_h1_count: int = 1
    min_h2_count: int = 3
    min_image_alt_ratio: float = 0.8
    alt_text_max_length: int = 125
    structure_weight: float = 20.0


@dataclass
class LinkRules:
    """
    链接规则配置 - 2025 Standard
    Source: Rush Analytics, Zyppy SEO study
    - 3-5 internal links per 1,000 words
    - Max 100-150 total links per page
    - Quality outbound links build trust
    """
    min_internal_links: int = 3
    optimal_internal_links_per_1000_words: int = 3
    max_internal_links_per_1000_words: int = 5
    min_external_links: int = 1
    max_total_links: int = 150
    weight: float = 7.0
    poor_anchor_texts: List[str] = field(default_factory=lambda: [
        "点击这里", "click here", "这里", "here", "link", "链接", "read more"
    ])


@dataclass
class EEATRules:
    """
    E-E-A-T 规则配置 - 2025 Google Standard
    Source: Google Search Central, Backlinko E-E-A-T Guide
    - Experience: First-hand knowledge, case studies
    - Expertise: Author credentials, technical depth
    - Authoritativeness: Citations, references, backlinks
    - Trustworthiness: Accuracy, transparency, security
    """
    require_author_info: bool = True
    require_publish_date: bool = True
    min_citations: int = 2
    min_external_references: int = 1
    weight: float = 10.0
    high_authority_domains: List[str] = field(default_factory=lambda: [
        "gov", "edu", "wikipedia.org", "docs.python.org", "developer.mozilla.org",
        "w3.org", "schema.org", "developers.google.com", "microsoft.com/docs"
    ])


@dataclass
class AISearchRules:
    """
    AI搜索优化规则 - 2025 Standard
    Source: Ahrefs 82-Point Checklist
    - FAQ sections for AI Overviews
    - Structured answers for featured snippets
    - Clear, concise answer blocks
    """
    check_faq_section: bool = True
    check_structured_answers: bool = True
    check_list_content: bool = True
    weight: float = 5.0
    first_paragraph_optimal_max_words: int = 120
    first_paragraph_min_words: int = 50
    faq_optimal_min: int = 3
    faq_optimal_max: int = 5
    faq_answer_min_words: int = 40
    faq_answer_max_words: int = 60
    summary_keywords: List[str] = field(default_factory=lambda: [
        "tldr", "tl;dr", "摘要", "summary", "key takeaways", "要点", "结论", "conclusion"
    ])


@dataclass
class IntentRules:
    """搜索意图匹配规则"""
    intent_keywords: List[str] = field(default_factory=lambda: [
        "指南", "教程", "如何", "怎么", "步骤", "Top 10", "最佳", "推荐", "清单", "guide", "how to", "best", "top", "checklist"
    ])
    intro_min_words: int = 30
    intro_max_words: int = 160
    conclusion_headings: List[str] = field(default_factory=lambda: [
        "结论", "总结", "小结", "结语", "Conclusion", "Final Thoughts", "Wrap Up"
    ])
    weight: float = 5.0


@dataclass
class ContentDepthRules:
    """
    内容深度配置（10x Content）
    """
    optimal_min_words: int = 1500
    optimal_max_words: int = 2500
    acceptable_max_words: int = 4000
    section_optimal_min: int = 4
    section_optimal_max: int = 8
    paragraph_min_words: int = 100
    paragraph_max_words: int = 200
    evidence_min_citations: int = 2
    evidence_min_data_points: int = 2


@dataclass
class ScoreWeights:
    """
    新评分权重（总分100）
    Schema移除：纯Markdown无结构化数据，新增意图匹配
    """
    metadata: float = 15.0
    intent: float = 5.0
    content_depth: float = 20.0
    eeat: float = 15.0
    structure: float = 15.0
    ai_search: float = 10.0
    keywords: float = 10.0
    schema: float = 0.0
    ai_semantic: float = 10.0


@dataclass
class MarkdownSEOConfig:
    """Markdown SEO配置主类 - 2025 Standards"""
    title: TitleRules = None
    description: DescriptionRules = None
    keywords: KeywordRules = None
    content: ContentRules = None
    links: LinkRules = None
    eeat: EEATRules = None
    ai_search: AISearchRules = None
    intent: IntentRules = None
    content_depth: ContentDepthRules = None
    score_weights: ScoreWeights = None

    # LLM配置
    llm_api_key: str = ""
    llm_base_url: str = "https://newapi.deepwisdom.ai/v1"
    llm_model: str = "gpt-4o"
    llm_timeout: int = 30
    llm_max_retries: int = 3
    enable_ai_analysis: bool = True

    def __post_init__(self):
        """初始化默认子配置和环境变量覆盖"""
        if self.title is None:
            self.title = TitleRules()
        if self.description is None:
            self.description = DescriptionRules()
        if self.keywords is None:
            self.keywords = KeywordRules()
        if self.content is None:
            self.content = ContentRules()
        if self.links is None:
            self.links = LinkRules()
        if self.eeat is None:
            self.eeat = EEATRules()
        if self.ai_search is None:
            self.ai_search = AISearchRules()
        if self.intent is None:
            self.intent = IntentRules()
        if self.content_depth is None:
            self.content_depth = ContentDepthRules()
        if self.score_weights is None:
            self.score_weights = ScoreWeights()

        # 环境变量覆盖
        self._apply_env_overrides()

    def _apply_env_overrides(self):
        """应用环境变量覆盖"""
        if os.getenv('MD_AUDIT_LLM_API_KEY'):
            self.llm_api_key = os.getenv('MD_AUDIT_LLM_API_KEY')
        if os.getenv('MD_AUDIT_LLM_BASE_URL'):
            self.llm_base_url = os.getenv('MD_AUDIT_LLM_BASE_URL')
        if os.getenv('MD_AUDIT_LLM_MODEL'):
            self.llm_model = os.getenv('MD_AUDIT_LLM_MODEL')
        if os.getenv('MD_AUDIT_ENABLE_AI'):
            self.enable_ai_analysis = os.getenv('MD_AUDIT_ENABLE_AI', '').lower() in ('true', '1', 'yes')

    @classmethod
    def from_json(cls, json_path: str) -> 'MarkdownSEOConfig':
        """从JSON文件加载配置"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 过滤掉comment字段
        def filter_comments(d):
            return {k: v for k, v in d.items() if k != 'comment'}

        config = cls(
            title=TitleRules(**filter_comments(data.get('title_rules', {}))),
            description=DescriptionRules(**filter_comments(data.get('description_rules', {}))),
            keywords=KeywordRules(**filter_comments(data.get('keyword_rules', {}))),
            content=ContentRules(**filter_comments(data.get('content_rules', {}))),
            links=LinkRules(**filter_comments(data.get('link_rules', {}))),
            eeat=EEATRules(**filter_comments(data.get('eeat_rules', {}))),
            ai_search=AISearchRules(**filter_comments(data.get('ai_search_rules', {}))),
            intent=IntentRules(**filter_comments(data.get('intent_rules', {}))) if data.get('intent_rules') else IntentRules(),
            content_depth=ContentDepthRules(**filter_comments(data.get('content_depth_rules', {}))),
            score_weights=ScoreWeights(**filter_comments(data.get('score_weights', {}))) if data.get('score_weights') else ScoreWeights(),
            llm_api_key=data.get('llm_api_key', ''),
            llm_base_url=data.get('llm_base_url', 'https://newapi.deepwisdom.ai/v1'),
            llm_model=data.get('llm_model', 'gpt-4o'),
            llm_timeout=data.get('llm_timeout', 30),
            llm_max_retries=data.get('llm_max_retries', 3),
            enable_ai_analysis=data.get('enable_ai_analysis', True),
        )

        config._apply_env_overrides()
        return config

    def to_json(self, json_path: str):
        """保存配置到JSON文件"""
        data = {
            'title_rules': asdict(self.title),
            'description_rules': asdict(self.description),
            'keyword_rules': asdict(self.keywords),
            'content_rules': asdict(self.content),
            'link_rules': asdict(self.links),
            'eeat_rules': asdict(self.eeat),
            'ai_search_rules': asdict(self.ai_search),
            'intent_rules': asdict(self.intent),
            'content_depth_rules': asdict(self.content_depth),
            'score_weights': asdict(self.score_weights),
            'llm_api_key': '',
            'llm_base_url': self.llm_base_url,
            'llm_model': self.llm_model,
            'llm_timeout': self.llm_timeout,
            'llm_max_retries': self.llm_max_retries,
            'enable_ai_analysis': self.enable_ai_analysis,
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def load_config(config_path: Optional[str] = None) -> MarkdownSEOConfig:
    """加载配置（优先级：自定义路径 > 默认路径）"""
    if config_path and Path(config_path).exists():
        return MarkdownSEOConfig.from_json(config_path)

    default_path = Path(__file__).parent.parent / "config" / "default_config.json"
    if default_path.exists():
        return MarkdownSEOConfig.from_json(str(default_path))

    return MarkdownSEOConfig()
