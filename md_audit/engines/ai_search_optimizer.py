"""
AI 搜索优化检测器（Google AI Overview / GEO）
"""
from __future__ import annotations

import re
from typing import Dict, List

from md_audit.config import MarkdownSEOConfig
from md_audit.models.data_models import DiagnosticItem, SeverityLevel, ParsedMarkdown


class AISearchOptimizer:
    """输出0-10分的AI搜索优化分"""

    def __init__(self, config: MarkdownSEOConfig):
        self.config = config
        self.rules = config.ai_search
        self.weights = {
            "direct_answer": 3,
            "faq": 3,
            "summary": 2,
            "structure": 2,
        }

    def analyze(self, parsed: ParsedMarkdown) -> Dict[str, object]:
        content = parsed.raw_content
        diagnostics: List[DiagnosticItem] = []

        direct_score = self._check_direct_answer(content)
        summary_score = self._check_summaries(content)
        faq_score = self._check_faq_structure(content)
        structure_score = self._check_structure(content)

        total = round(direct_score + summary_score + faq_score + structure_score, 2)

        diagnostics.append(self._build_diag(
            "ai_search", "direct_answer", direct_score, self.weights["direct_answer"],
            "首段直接答案检测完成", "首段50-120词内回答核心问题，并出现核心关键词。"
        ))
        diagnostics.append(self._build_diag(
            "ai_search", "summary", summary_score, self.weights["summary"],
            "总结/要点检测完成", "增加 TL;DR/Key Takeaways 或文末结论，并用列表呈现要点。"
        ))
        diagnostics.append(self._build_diag(
            "ai_search", "faq", faq_score, self.weights["faq"],
            "FAQ 结构检测完成", "添加3-5个问答，问题以?结尾，答案40-60词。"
        ))
        diagnostics.append(self._build_diag(
            "ai_search", "structured_format", structure_score, self.weights["structure"],
            "结构化格式检测完成", "使用列表/表格/步骤化格式，便于AI提取。"
        ))

        return {
            "direct_answer_score": direct_score,
            "summary_score": summary_score,
            "faq_score": faq_score,
            "structured_format_score": structure_score,
            "citability_score": 0.0,
            "total_geo_score": total,
            "optimization_tips": self._tips(diagnostics),
            "diagnostics": diagnostics,
        }

    def _check_direct_answer(self, content: str) -> float:
        """首段直接答案，满分3"""
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if not paragraphs:
            return 0.0
        first_para = paragraphs[0]
        words = len(first_para.split())
        if words == 0:
            return 0.0

        if self.rules.first_paragraph_min_words <= words <= self.rules.first_paragraph_optimal_max_words:
            base = 2.0
        elif words < self.rules.first_paragraph_min_words:
            base = 1.0
        else:
            base = 1.5

        # 是否包含明确答案陈述
        if re.search(r'(答案是|结论是|可以直接|简而言之|in short|the answer is)', first_para, re.IGNORECASE):
            base += 1.0
        return round(min(base, self.weights["direct_answer"]), 2)

    def _check_summaries(self, content: str) -> float:
        """总结/要点，满分2"""
        lines = content.splitlines()
        summary_patterns = [p for p in self.rules.summary_keywords]
        has_summary = any(re.search(p, line, re.IGNORECASE) for line in lines for p in summary_patterns)
        bullet_summary = re.search(r'^[-*+]\s+.+', content, re.MULTILINE) is not None
        score = 0.0
        if has_summary:
            score += 1.2
        if bullet_summary:
            score += 0.8
        return round(min(score, self.weights["summary"]), 2)

    def _check_faq_structure(self, content: str) -> float:
        """FAQ 结构，满分3"""
        faq_patterns = [
            r'^#+\s*(FAQ|常见问题|Q&A|问答)',
            r'^#+\s*.*\?$',  # 问号结尾标题
        ]
        has_faq_heading = any(re.search(p, content, re.IGNORECASE | re.MULTILINE) for p in faq_patterns)
        questions = re.findall(r'^#+\s*(.+\?)$', content, re.MULTILINE)
        score = 0.0
        if has_faq_heading:
            score += 1.5
        faq_count = len(questions)
        if self.rules.faq_optimal_min <= faq_count <= self.rules.faq_optimal_max:
            score += 1.0
        elif faq_count > 0:
            score += 0.5

        # 答案长度检测（粗略通过行距判断）
        answers = re.findall(r'\?\s*\n+([^\n]+)', content)
        good_answers = [
            a for a in answers
            if self.rules.faq_answer_min_words <= len(a.split()) <= self.rules.faq_answer_max_words
        ]
        if answers:
            ratio = len(good_answers) / len(answers)
            if ratio >= 0.6:
                score += 0.5
            elif ratio > 0:
                score += 0.2
        return round(min(score, self.weights["faq"]), 2)

    def _check_structure(self, content: str) -> float:
        """结构化格式，满分2"""
        has_list = re.search(r'^[-*+]\s+.+', content, re.MULTILINE)
        has_number_list = re.search(r'^\d+\.\s+.+', content, re.MULTILINE)
        has_table = "|" in content and re.search(r'\|.*\|', content)
        score = 0.0
        if has_list or has_number_list:
            score += 1.0
        if has_table:
            score += 0.5
        if re.search(r'(步骤|step\s*\d+|流程)', content, re.IGNORECASE):
            score += 0.5
        return round(min(score, self.weights["structure"]), 2)

    def _severity_from_score(self, score: float, max_score: float) -> SeverityLevel:
        ratio = score / max_score if max_score else 0
        if ratio >= 0.85:
            return SeverityLevel.SUCCESS
        if ratio >= 0.6:
            return SeverityLevel.INFO
        if ratio >= 0.3:
            return SeverityLevel.WARNING
        return SeverityLevel.CRITICAL

    def _build_diag(self, category: str, name: str, score: float, max_score: float, message: str, suggestion: str) -> DiagnosticItem:
        return DiagnosticItem(
            category=category,
            check_name=name,
            severity=self._severity_from_score(score, max_score),
            score=round(score, 2),
            message=message,
            suggestion=suggestion,
            expected_value=str(max_score)
        )

    def _tips(self, diags: List[DiagnosticItem]) -> List[str]:
        """将低分项转化为优化提示"""
        tips = []
        for d in diags:
            if d.severity in (SeverityLevel.WARNING, SeverityLevel.CRITICAL):
                tips.append(d.suggestion)
        return tips
