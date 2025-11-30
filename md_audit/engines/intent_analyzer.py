"""
搜索意图匹配分析器
"""
from __future__ import annotations

import re
from typing import Dict, List

from md_audit.config import MarkdownSEOConfig
from md_audit.models.data_models import DiagnosticItem, SeverityLevel, ParsedMarkdown


class IntentAnalyzer:
    """搜索意图匹配 - 最高5分"""

    def __init__(self, config: MarkdownSEOConfig):
        self.config = config
        self.rules = config.intent
        self.weight = config.score_weights.intent

    def analyze(self, parsed: ParsedMarkdown) -> Dict[str, object]:
        content = parsed.raw_content
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        intro = paragraphs[0] if paragraphs else ""

        intent_score, intent_diag = self._check_intent(parsed.title, intro)
        intro_score, intro_diag = self._check_intro(intro)
        conclusion_score, conclusion_diag = self._check_conclusion(content)

        total = round(intent_score + intro_score + conclusion_score, 2)
        diagnostics = [intent_diag, intro_diag, conclusion_diag]

        suggestions = [d.suggestion for d in diagnostics if d.severity in (SeverityLevel.WARNING, SeverityLevel.CRITICAL)]

        return {
            "intent_score": total,
            "details": {
                "intent_keywords_score": intent_score,
                "intro_score": intro_score,
                "conclusion_score": conclusion_score,
            },
            "diagnostics": diagnostics,
            "suggestions": suggestions,
        }

    def _check_intent(self, title: str, intro: str):
        """检测意图词出现，满分2分"""
        intent_words = self.rules.intent_keywords
        pattern = "|".join(re.escape(w) for w in intent_words)
        found_in_title = re.search(pattern, title, re.IGNORECASE)
        found_in_intro = re.search(pattern, intro, re.IGNORECASE)

        score = 0.0
        if found_in_title:
            score += 1.2
        if found_in_intro:
            score += 0.8
        score = min(2.0, score)

        severity = self._severity(score, 2.0)
        diag = DiagnosticItem(
            category="intent",
            check_name="intent_keywords",
            severity=severity,
            score=round(score, 2),
            message="检测标题/引言意图词",
            suggestion="在标题或首段添加‘指南/如何/Top 10/最佳’等意图词，明确读者预期。",
            expected_value=">=1个意图词"
        )
        return score, diag

    def _check_intro(self, intro: str):
        """检测引言是否简短直陈，满分2分"""
        words = len(intro.split())
        if words == 0:
            score = 0.0
        elif self.rules.intro_min_words <= words <= self.rules.intro_max_words:
            score = 2.0
        else:
            score = 1.0

        severity = self._severity(score, 2.0)
        diag = DiagnosticItem(
            category="intent",
            check_name="intro_clarity",
            severity=severity,
            score=round(score, 2),
            message=f"引言长度 {words} 词",
            suggestion=f"引言建议 {self.rules.intro_min_words}-{self.rules.intro_max_words} 词，直接给出阅读收获。",
            expected_value=f"{self.rules.intro_min_words}-{self.rules.intro_max_words}词"
        )
        return score, diag

    def _check_conclusion(self, content: str):
        """检测是否存在结论/总结段，满分1分"""
        headings = self.rules.conclusion_headings
        pattern = r'^#+\s*(%s)' % "|".join(re.escape(h) for h in headings)
        has_conclusion = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        score = 1.0 if has_conclusion else 0.0
        severity = self._severity(score, 1.0)
        diag = DiagnosticItem(
            category="intent",
            check_name="conclusion_presence",
            severity=severity,
            score=round(score, 2),
            message="检测结论/总结章节",
            suggestion="长文应包含“结论/总结/Conclusion”章节，重申要点与行动项。",
            expected_value="存在结论段"
        )
        return score, diag

    def _severity(self, score: float, max_score: float) -> SeverityLevel:
        ratio = score / max_score if max_score else 0
        if ratio >= 0.85:
            return SeverityLevel.SUCCESS
        if ratio >= 0.6:
            return SeverityLevel.INFO
        if ratio >= 0.3:
            return SeverityLevel.WARNING
        return SeverityLevel.CRITICAL
