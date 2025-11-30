"""
内容深度分析器 - 10x Content 标准
"""
from __future__ import annotations

import re
from typing import Dict, List

from md_audit.models.data_models import DiagnosticItem, SeverityLevel, ParsedMarkdown
from md_audit.config import MarkdownSEOConfig


class ContentDepthAnalyzer:
    """内容深度分析器，输出0-20分"""

    def __init__(self, config: MarkdownSEOConfig):
        self.config = config
        self.rules = config.content_depth
        self.weights = {
            "word_count": 6,
            "sections": 5,
            "readability": 4,
            "evidence": 5,
        }

    def analyze(self, parsed: ParsedMarkdown) -> Dict[str, object]:
        paragraphs = self._split_paragraphs(parsed.raw_content)
        h3_tags = self._extract_h3(parsed.html_content)
        details = {}
        diagnostics: List[DiagnosticItem] = []
        suggestions: List[str] = []

        word_score = self._score_word_count(parsed.word_count)
        details["word_count_score"] = word_score
        diagnostics.append(self._build_diag(
            category="content_depth",
            name="word_count",
            score=word_score,
            max_score=self.weights["word_count"],
            message=f"当前词数 {parsed.word_count}",
            suggestion=self._word_suggestion(parsed.word_count),
            severity=self._severity_from_score(word_score, self.weights["word_count"])
        ))

        section_score = self._score_sections(len(parsed.h2_tags), len(h3_tags))
        details["section_depth_score"] = section_score
        diagnostics.append(self._build_diag(
            category="content_depth",
            name="section_depth",
            score=section_score,
            max_score=self.weights["sections"],
            message=f"H2:{len(parsed.h2_tags)} H3:{len(h3_tags)}",
            suggestion="建议保持4-8个H2，每个H2下1-3个H3，形成层次化结构",
            severity=self._severity_from_score(section_score, self.weights["sections"])
        ))

        readability_score = self._score_readability(paragraphs)
        details["readability_score"] = readability_score
        diagnostics.append(self._build_diag(
            category="content_depth",
            name="paragraph_readability",
            score=readability_score,
            max_score=self.weights["readability"],
            message="段落长度检测完成",
            suggestion="每段100-200词最优，过长可拆分小节，过短补充细节",
            severity=self._severity_from_score(readability_score, self.weights["readability"])
        ))

        evidence_score = self._score_evidence(parsed.raw_content, parsed.links)
        details["evidence_score"] = evidence_score
        diagnostics.append(self._build_diag(
            category="content_depth",
            name="evidence_support",
            score=evidence_score,
            max_score=self.weights["evidence"],
            message="数据/案例/引用检测完成",
            suggestion="至少添加2处数据点与2个外部引用，技术文可补充代码示例",
            severity=self._severity_from_score(evidence_score, self.weights["evidence"])
        ))

        total_depth_score = round(sum(details.values()), 1)

        # 生成建议列表（简洁 actionable）
        if word_score < self.weights["word_count"]:
            suggestions.append(self._word_suggestion(parsed.word_count))
        if section_score < self.weights["sections"]:
            suggestions.append("补足章节：保持4-8个H2，每个H2下1-3个H3，增加层次感。")
        if readability_score < self.weights["readability"]:
            suggestions.append("调整段落长度到100-200词，避免大段堆砌或过度碎片。")
        if evidence_score < self.weights["evidence"]:
            suggestions.append("补充案例/数据并标注来源，至少2个外链指向权威站点。")

        return {
            "total_depth_score": total_depth_score,
            "details": details,
            "suggestions": suggestions,
            "diagnostics": diagnostics,
        }

    def _score_word_count(self, count: int) -> float:
        """按词数区间评分，满分6"""
        if count < 500:
            ratio = 0
        elif count < 1000:
            ratio = 0.4
        elif count < 1500:
            ratio = 0.7
        elif self.rules.optimal_min_words <= count <= self.rules.optimal_max_words:
            ratio = 1.0
        elif count <= self.rules.acceptable_max_words:
            ratio = 0.9
        else:
            ratio = 0.8
        return round(self.weights["word_count"] * ratio, 2)

    def _score_sections(self, h2_count: int, h3_count: int) -> float:
        """根据H2/H3层级评分，满分5"""
        score = 0.0
        if h2_count == 0:
            return 0.0
        if self.rules.section_optimal_min <= h2_count <= self.rules.section_optimal_max:
            score += 3.5
        elif 1 <= h2_count < self.rules.section_optimal_min:
            score += 2.0
        else:
            score += 2.5

        # H3密度：每个H2 1-3 个最优
        if h2_count > 0:
            avg_h3 = h3_count / h2_count if h2_count else 0
            if 1 <= avg_h3 <= 3:
                score += 1.5
            elif 0 < avg_h3 < 1:
                score += 0.8
            else:
                score += 0.5
        return round(min(score, self.weights["sections"]), 2)

    def _score_readability(self, paragraphs: List[str]) -> float:
        """段落长度评分，满分4"""
        if not paragraphs:
            return 0.0
        word_counts = [len(p.split()) for p in paragraphs]
        optimal = [self.rules.paragraph_min_words <= wc <= self.rules.paragraph_max_words for wc in word_counts]
        optimal_ratio = sum(1 for ok in optimal if ok) / len(word_counts)
        if optimal_ratio >= 0.8:
            ratio = 1.0
        elif optimal_ratio >= 0.5:
            ratio = 0.7
        elif optimal_ratio > 0:
            ratio = 0.4
        else:
            ratio = 0.0
        return round(self.weights["readability"] * ratio, 2)

    def _score_evidence(self, content: str, links: List[dict]) -> float:
        """证据与引用评分，满分5"""
        score = 0.0
        # 数据点：百分比、年份、具体数字
        data_points = re.findall(r'(\d{4}|\d+\.\d+%|\d+%)', content)
        if len(data_points) >= self.rules.evidence_min_data_points:
            score += 2.0
        elif data_points:
            score += 1.0

        # 外部引用：统计外链
        external_links = [l for l in links if l.get("href", "").startswith(("http://", "https://"))]
        if len(external_links) >= self.rules.evidence_min_citations:
            score += 2.0
        elif external_links:
            score += 1.0

        # 代码示例或公式
        has_code = "```" in content
        if has_code:
            score += 0.5

        # 表格/列表结构
        if re.search(r'^\\s*[-*+]|^\\s*\\d+\\.', content, re.MULTILINE):
            score += 0.5

        return round(min(score, self.weights["evidence"]), 2)

    def _split_paragraphs(self, content: str) -> List[str]:
        """按空行切分段落"""
        parts = [p.strip() for p in content.split("\n\n") if p.strip()]
        return parts

    def _extract_h3(self, html: str) -> List[str]:
        """从HTML中提取H3文本"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return []
        soup = BeautifulSoup(html, "html.parser")
        return [h3.get_text(strip=True) for h3 in soup.find_all("h3")]

    def _word_suggestion(self, count: int) -> str:
        """生成针对词数的建议"""
        if count < self.rules.optimal_min_words:
            gap = self.rules.optimal_min_words - count
            return f"当前 {count} 词，低于最佳区间 {self.rules.optimal_min_words}-{self.rules.optimal_max_words}。建议补充{gap}词以上，增加2-3个深度小节。"
        if count > self.rules.optimal_max_words:
            return f"当前 {count} 词，略高于最佳区间 {self.rules.optimal_min_words}-{self.rules.optimal_max_words}，可精简冗余段落或合并相似内容。"
        return "词数处于最佳区间，保持深度与结构即可。"

    def _severity_from_score(self, score: float, max_score: float) -> SeverityLevel:
        """根据得分映射严重级别"""
        ratio = score / max_score if max_score else 0
        if ratio >= 0.85:
            return SeverityLevel.SUCCESS
        if ratio >= 0.6:
            return SeverityLevel.INFO
        if ratio >= 0.3:
            return SeverityLevel.WARNING
        return SeverityLevel.CRITICAL

    def _build_diag(
        self,
        category: str,
        name: str,
        score: float,
        max_score: float,
        message: str,
        suggestion: str,
        severity: SeverityLevel,
    ) -> DiagnosticItem:
        """构建诊断项（关键逻辑保持中文注释）"""
        return DiagnosticItem(
            category=category,
            check_name=name,
            severity=severity,
            score=round(score, 2),
            message=message,
            suggestion=suggestion,
            expected_value=str(max_score)
        )
