"""
AI语义分析引擎 - 2025 SEO Standards
基于 Ahrefs, SEMrush, Backlinko 权威标准

评分维度（40分满分）：
- E-E-A-T评估: 15分（经验/专业/权威/可信）
- 内容深度与价值: 15分（实用性/独特性/覆盖度）
- 可读性与AI搜索优化: 10分（结构/FAQ/Featured Snippets适配）
"""

import os
import time
import json
import re
from typing import Optional
from openai import OpenAI, APIError, RateLimitError, APITimeoutError, APIConnectionError
from md_audit.models.data_models import AIAnalysisResult, EEATDetails, ParsedMarkdown
from md_audit.config import MarkdownSEOConfig


class AIEngine:
    """AI语义分析引擎（2025 SEO Standards）"""

    def __init__(self, config: MarkdownSEOConfig):
        self.config = config

        if not config.llm_api_key:
            raise ValueError("LLM API Key未设置，请通过环境变量MD_AUDIT_LLM_API_KEY提供")

        self.client = OpenAI(
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            timeout=config.llm_timeout
        )

    def analyze(self, parsed: ParsedMarkdown, keywords: list[str]) -> Optional[AIAnalysisResult]:
        """
        AI语义分析（2025 SEO Standards）

        评估标准基于：
        - Google E-E-A-T Quality Rater Guidelines 2025
        - Ahrefs 82-Point SEO Checklist
        - Backlinko Content Study (Top 10平均1447词)
        - SEMrush On-Page SEO Guide

        Args:
            parsed: 解析后的Markdown数据
            keywords: 关键词列表

        Returns:
            AI分析结果，失败时返回None
        """
        if not self.config.enable_ai_analysis:
            return None

        # 构造2025 SEO标准prompt
        keyword_str = "、".join(keywords) if keywords else "未提供"

        # 提取结构信息（更细化，便于拉开分差）
        h1_count = len(parsed.h1_tags)
        h2_count = len(parsed.h2_tags) if hasattr(parsed, 'h2_tags') else 0
        h3_count = len(parsed.h3_tags) if hasattr(parsed, 'h3_tags') else 0
        link_count = len(parsed.links)
        internal_links = [l for l in parsed.links if not l.get('href', '').startswith(('http://', 'https://'))]
        external_links = [l for l in parsed.links if l.get('href', '').startswith(('http://', 'https://'))]
        image_count = len(parsed.images)

        # FAQ / 结论检测
        has_faq = bool(re.search(r'(^#+\\s*(FAQ|常见问题|Q&A))', parsed.raw_content, re.IGNORECASE | re.MULTILINE))
        has_conclusion = bool(re.search(r'(^#+\\s*(结论|总结|Conclusion|Final Thoughts|Wrap Up))', parsed.raw_content, re.IGNORECASE | re.MULTILINE))

        # 可读性基础统计
        sentences = re.split(r'[.!?。！？]\\s*', parsed.raw_content)
        sentences = [s.strip() for s in sentences if s.strip()]
        avg_sentence_len = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0

        paragraphs = [p.strip() for p in parsed.raw_content.split('\\n\\n') if p.strip()]
        avg_paragraph_words = sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0

        content_sample = parsed.raw_content[:2000]
        if len(parsed.raw_content) > 2500:
            content_sample += "\n\n[...中间内容省略...]\n\n" + parsed.raw_content[-500:]

        prompt = f"""
你是严苛的SEO评审官，必须拉开分差，禁止礼貌性给分。

## 文章元数据
- 标题：{parsed.title}（{len(parsed.title)}字符）
- 描述：{parsed.description}（{len(parsed.description)}字符）
- 关键词：{keyword_str}
- 字数：{parsed.word_count}

## 结构与可读性信号（缺失要素必须扣分）
- H1: {h1_count}，H2: {h2_count}，H3: {h3_count}
- 内链: {len(internal_links)}，外链: {len(external_links)}，总链接: {link_count}
- FAQ: {'有' if has_faq else '无'}；结论: {'有' if has_conclusion else '无'}
- 平均句长: {avg_sentence_len:.1f} 词；平均段落词数: {avg_paragraph_words:.1f}
- 图片: {image_count}

## 强制扣分上限（硬约束）
- H2 = 0 → readability_score ≤ 40
- 内链 = 0 → topical_relevance_score ≤ 60
- 字数 < 800 → depth_score ≤ 45；字数 < 1200 → depth_score ≤ 55
- 无作者或日期 → eeat_score ≤ 55

## 参考档位（用于区分高低分）
- 85-100：H2/H3完整，FAQ+结论齐全，内链≥3，原创数据/案例，作者与日期明确。
- 60-75：结构基本完整但缺少部分要素（FAQ/结论/案例/内链不足），信息较浅。
- 40-55：H2缺失或极少，内链为0，无作者日期，无案例，无FAQ/结论。

## 采样内容（前2000词 + 末尾500词）
{content_sample}

仅输出 JSON：{{
  "eeat_score": 0-100,
  "depth_score": 0-100,
  "readability_score": 0-100,
  "topical_relevance_score": 0-100,
  "overall_feedback": "50字以内核心诊断",
  "improvement_suggestions": ["建议1","建议2","建议3"],
  "eeat_details": {{"experience":"","expertise":"","authoritativeness":"","trustworthiness":""}},
  "ai_search_optimization": {{"featured_snippet_ready": true/false, "ai_overview_friendly": true/false, "suggestion": "30字内"}}
}}
"""

        # 重试机制
        for attempt in range(self.config.llm_max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.llm_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是严格的SEO评审官，遵循E-E-A-T与Helpful Content原则，必须拉开分差，不给安全分，缺失要素要显著扣分。"
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    response_format={"type": "json_object"}
                )

                # 解析响应
                result_text = response.choices[0].message.content
                result_data = json.loads(result_text)

                # 解析E-E-A-T详细评价
                eeat_details = None
                if 'eeat_details' in result_data and result_data['eeat_details']:
                    eeat_details = EEATDetails(
                        experience=result_data['eeat_details'].get('experience', ''),
                        expertise=result_data['eeat_details'].get('expertise', ''),
                        authoritativeness=result_data['eeat_details'].get('authoritativeness', ''),
                        trustworthiness=result_data['eeat_details'].get('trustworthiness', '')
                    )

                # 验证并返回（2025 SEO标准）
                return AIAnalysisResult(
                    eeat_score=float(result_data.get('eeat_score', 0)),
                    depth_score=float(result_data.get('depth_score', 0)),
                    readability_score=float(result_data.get('readability_score', 0)),
                    topical_relevance_score=float(result_data.get('topical_relevance_score', 0)),
                    # 兼容旧字段
                    relevance_score=float(result_data.get('topical_relevance_score', result_data.get('relevance_score', 0))),
                    overall_feedback=result_data.get('overall_feedback', ''),
                    improvement_suggestions=result_data.get('improvement_suggestions', []),
                    eeat_details=eeat_details
                )

            except json.JSONDecodeError as e:
                print(f"[警告] AI返回结果解析失败（尝试 {attempt+1}/{self.config.llm_max_retries}）：{e}")
                if attempt < self.config.llm_max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                continue

            except RateLimitError as e:
                print(f"[警告] API限流（尝试 {attempt+1}/{self.config.llm_max_retries}）：{e}")
                if attempt < self.config.llm_max_retries - 1:
                    time.sleep(5 * (2 ** attempt))  # 限流时更长等待
                continue

            except APITimeoutError as e:
                print(f"[警告] API超时（尝试 {attempt+1}/{self.config.llm_max_retries}）：{e}")
                if attempt < self.config.llm_max_retries - 1:
                    time.sleep(2 ** attempt)
                continue

            except APIConnectionError as e:
                print(f"[警告] API连接失败（尝试 {attempt+1}/{self.config.llm_max_retries}）：{e}")
                if attempt < self.config.llm_max_retries - 1:
                    time.sleep(2 ** attempt)
                continue

            except APIError as e:
                print(f"[警告] API错误（尝试 {attempt+1}/{self.config.llm_max_retries}）：{e}")
                if attempt < self.config.llm_max_retries - 1:
                    time.sleep(2 ** attempt)
                continue

            except Exception as e:
                print(f"[错误] 未知异常（尝试 {attempt+1}/{self.config.llm_max_retries}）：{type(e).__name__}: {e}")
                if attempt < self.config.llm_max_retries - 1:
                    time.sleep(2 ** attempt)
                continue

        # 所有重试都失败
        print("[错误] AI分析失败，已达到最大重试次数，将跳过AI评分")
        return None

    def calculate_ai_score(self, ai_result: Optional[AIAnalysisResult]) -> float:
        """
        计算AI内容质量得分（满分40分）- 2025 SEO Standards

        评分权重（基于2025 Google算法权重）：
        - E-E-A-T评估: 37.5% (15/40) - Google核心排名因素
        - 内容深度与价值: 37.5% (15/40) - Helpful Content核心
        - 可读性与AI搜索优化: 25% (10/40) - 用户体验+AI Overview

        Args:
            ai_result: AI分析结果

        Returns:
            AI得分（0-40）
        """
        if not ai_result:
            return 0.0

        # 2025 SEO权重分配
        # E-E-A-T: 15分 (37.5%) - 2025 Google核心排名因素
        # 内容深度: 15分 (37.5%) - Helpful Content Update核心
        # 可读性+AI优化: 10分 (25%) - UX + AI Overview适配
        eeat_contribution = (ai_result.eeat_score / 100) * 15
        depth_contribution = (ai_result.depth_score / 100) * 15
        readability_contribution = (ai_result.readability_score / 100) * 10

        total = eeat_contribution + depth_contribution + readability_contribution
        return round(total, 1)
