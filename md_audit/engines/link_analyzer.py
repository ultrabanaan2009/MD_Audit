"""
链接质量分析器
"""
from __future__ import annotations

from typing import Dict, List

from md_audit.config import MarkdownSEOConfig
from md_audit.models.data_models import DiagnosticItem, SeverityLevel


class LinkAnalyzer:
    """链接质量分析，输出0-3分（结构子维度）"""

    def __init__(self, config: MarkdownSEOConfig):
        self.config = config
        self.rules = config.links

    def analyze(self, links: List[dict], word_count: int) -> Dict[str, object]:
        internal_links = [l for l in links if not l.get("href", "").startswith(("http://", "https://"))]
        external_links = [l for l in links if l.get("href", "").startswith(("http://", "https://"))]

        diagnostics: List[DiagnosticItem] = []

        internal_score = self._score_internal_links(internal_links, word_count)
        external_score = self._score_external_links(external_links)
        anchor_score = self._score_anchor_texts(links)

        total = round(internal_score + external_score + anchor_score, 2)

        diagnostics.append(self._diag(
            "links", "internal_links", internal_score, 1.5,
            f"内链 {len(internal_links)} 条",
            f"建议保持每千词{self.rules.optimal_internal_links_per_1000_words}-{self.rules.max_internal_links_per_1000_words}个内链。"
        ))
        diagnostics.append(self._diag(
            "links", "external_links", external_score, 1.0,
            f"外链 {len(external_links)} 条",
            "确保引用2-5个权威来源，提升可信度。"
        ))
        diagnostics.append(self._diag(
            "links", "anchor_text", anchor_score, 0.5,
            "锚文本质量检测完成",
            "使用描述性锚文本，避免“点击这里”“link”等泛化用语。"
        ))

        return {
            "internal_link_score": internal_score,
            "external_link_score": external_score,
            "anchor_text_quality": anchor_score,
            "total_link_score": total,
            "suggestions": [d.suggestion for d in diagnostics if d.severity in (SeverityLevel.WARNING, SeverityLevel.CRITICAL)],
            "diagnostics": diagnostics,
        }

    def _score_internal_links(self, internal_links: List[dict], word_count: int) -> float:
        """内链密度评分，满分1.5"""
        words_in_k = word_count / 1000 if word_count else 1
        density = len(internal_links) / words_in_k
        if self.rules.optimal_internal_links_per_1000_words <= density <= self.rules.max_internal_links_per_1000_words:
            return 1.5
        if density == 0:
            return 0.3
        if density < self.rules.optimal_internal_links_per_1000_words:
            return 1.0
        return 0.8  # 过多稍减分

    def _score_external_links(self, external_links: List[dict]) -> float:
        """外链质量评分，满分1.0"""
        count = len(external_links)
        if self.rules.min_external_links <= count <= 5:
            return 1.0
        if count == 0:
            return 0.0
        return 0.6  # 数量不足或超标

    def _score_anchor_texts(self, links: List[dict]) -> float:
        """锚文本质量评分，满分0.5"""
        if not links:
            return 0.3
        poor = 0
        bare = 0
        for link in links:
            text = (link.get("text") or "").strip().lower()
            href = link.get("href", "")
            if not text:
                bare += 1
            if any(p in text for p in self.rules.poor_anchor_texts):
                poor += 1
            if href and href == text:
                bare += 1
        ratio_bad = (poor + bare) / len(links)
        if ratio_bad == 0:
            return 0.5
        if ratio_bad <= 0.3:
            return 0.35
        if ratio_bad <= 0.6:
            return 0.2
        return 0.1

    def _severity_from_score(self, score: float, max_score: float) -> SeverityLevel:
        ratio = score / max_score if max_score else 0
        if ratio >= 0.85:
            return SeverityLevel.SUCCESS
        if ratio >= 0.6:
            return SeverityLevel.INFO
        if ratio >= 0.3:
            return SeverityLevel.WARNING
        return SeverityLevel.CRITICAL

    def _diag(self, category: str, name: str, score: float, max_score: float, message: str, suggestion: str) -> DiagnosticItem:
        return DiagnosticItem(
            category=category,
            check_name=name,
            severity=self._severity_from_score(score, max_score),
            score=round(score, 2),
            message=message,
            suggestion=suggestion,
            expected_value=str(max_score)
        )
