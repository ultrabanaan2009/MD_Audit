"""
E-E-A-T 信号分析器
"""
from __future__ import annotations

import re
from typing import Dict, List

from md_audit.config import MarkdownSEOConfig
from md_audit.models.data_models import DiagnosticItem, SeverityLevel, ParsedMarkdown


class EEATAnalyzer:
    """输出0-15分的E-E-A-T评估"""

    def __init__(self, config: MarkdownSEOConfig):
        self.config = config
        self.rules = config.eeat
        self.weights = {
            "experience": 4,
            "expertise": 4,
            "authority": 4,
            "trust": 3,
        }

    def analyze(self, parsed: ParsedMarkdown) -> Dict[str, object]:
        content = parsed.raw_content
        frontmatter = parsed.frontmatter
        diagnostics: List[DiagnosticItem] = []
        missing_signals: List[str] = []

        experience_score = self._detect_experience(content)
        expertise_score = self._detect_expertise(content)
        authority_score = self._detect_authority(content, parsed.links, frontmatter)
        trust_score = self._detect_trust(content, frontmatter)

        total = round(experience_score + expertise_score + authority_score + trust_score, 2)

        # 生成诊断
        diagnostics.append(self._build_diag(
            "eeat", "experience", experience_score, self.weights["experience"],
            "经验信号检测完成：第一人称/案例/时间线", self._exp_suggestion(experience_score)
        ))
        diagnostics.append(self._build_diag(
            "eeat", "expertise", expertise_score, self.weights["expertise"],
            "专业性检测完成：术语/代码/步骤化方法", self._expertise_suggestion(expertise_score)
        ))
        diagnostics.append(self._build_diag(
            "eeat", "authority", authority_score, self.weights["authority"],
            "权威性检测完成：作者信息/高权威引用", self._authority_suggestion(authority_score)
        ))
        diagnostics.append(self._build_diag(
            "eeat", "trust", trust_score, self.weights["trust"],
            "可信度检测完成：日期/来源标注/披露", self._trust_suggestion(trust_score)
        ))

        for diag in diagnostics:
            if diag.severity in (SeverityLevel.WARNING, SeverityLevel.CRITICAL):
                missing_signals.append(diag.check_name)

        return {
            "experience_score": experience_score,
            "expertise_score": expertise_score,
            "authority_score": authority_score,
            "trust_score": trust_score,
            "total_eeat_score": total,
            "missing_signals": missing_signals,
            "diagnostics": diagnostics,
        }

    def _detect_experience(self, content: str) -> float:
        """检测经验信号，满分4"""
        patterns = {
            "first_person": r"(I've|I have|我曾|我们团队|我们|我在|本人|in my experience)",
            "case_study": r"(案例|case study|实践经验|真实项目|client|实战)",
            "timeline": r"(过去\d+年|since \d{4}|多年来|years of experience)",
        }
        hits = sum(1 for p in patterns.values() if re.search(p, content, re.IGNORECASE))
        if hits >= 3:
            return 4.0
        if hits == 2:
            return 3.0
        if hits == 1:
            return 2.0
        return 0.0

    def _detect_expertise(self, content: str) -> float:
        """检测专业性信号，满分4"""
        score = 0.0
        # 术语密度：出现代码块或专业术语
        has_code = "```" in content or re.search(r'<code>|</code>', content, re.IGNORECASE)
        if has_code:
            score += 1.5
        if re.search(r'(算法|复杂度|API|SDK|架构|模型|正则|公式|benchmark)', content, re.IGNORECASE):
            score += 1.0
        if re.search(r'(步骤|step\s*\d+|流程|流程图|方法论|checklist)', content, re.IGNORECASE):
            score += 0.8
        if re.search(r'(图表|表格|数据集|实验|对照|验证)', content, re.IGNORECASE):
            score += 0.7
        return round(min(score, self.weights["expertise"]), 2)

    def _detect_authority(self, content: str, links: List[dict], frontmatter: dict) -> float:
        """检测权威性信号，满分4"""
        score = 0.0
        author = frontmatter.get("author") or frontmatter.get("author_name")
        author_bio = frontmatter.get("author_bio")
        if author:
            score += 1.0
        if author_bio:
            score += 0.5

        # 高权威域名引用
        external_links = [l.get("href", "") for l in links if l.get("href", "").startswith(("http://", "https://"))]
        high_quality = [l for l in external_links if self._is_high_authority(l)]
        medium_quality = [l for l in external_links if not self._is_low_quality(l) and l not in high_quality]

        if len(high_quality) >= 2:
            score += 1.5
        elif high_quality:
            score += 1.0
        if medium_quality:
            score += 0.5

        return round(min(score, self.weights["authority"]), 2)

    def _detect_trust(self, content: str, frontmatter: dict) -> float:
        """检测可信度，满分3"""
        score = 0.0
        date_fields = ['date', 'published', 'created', 'updated', 'lastmod']
        has_date = any(frontmatter.get(f) for f in date_fields)
        if has_date or re.search(r'(发布于|last updated|更新于|\d{4}-\d{1,2}-\d{1,2})', content, re.IGNORECASE):
            score += 1.2

        if re.search(r'(来源|source|reference|参考|数据来自)', content, re.IGNORECASE):
            score += 1.0

        if re.search(r'(免责声明|disclaimer|风险提示|声明|联系|contact)', content, re.IGNORECASE):
            score += 0.8

        return round(min(score, self.weights["trust"]), 2)

    def _is_high_authority(self, url: str) -> bool:
        """判断是否为高权威域名"""
        return any(domain in url for domain in self.rules.high_authority_domains)

    def _is_low_quality(self, url: str) -> bool:
        """简单判断低质量域名"""
        return any(p in url for p in ["blogspot", "medium.com/@", "forum", "reddit"])

    def _severity_from_score(self, score: float, max_score: float) -> SeverityLevel:
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
    ) -> DiagnosticItem:
        return DiagnosticItem(
            category=category,
            check_name=name,
            severity=self._severity_from_score(score, max_score),
            score=round(score, 2),
            message=message,
            suggestion=suggestion,
            expected_value=str(max_score)
        )

    def _exp_suggestion(self, score: float) -> str:
        if score >= 3.5:
            return "经验信号充分，保持第一人称与案例输出。"
        return "补充第一人称案例或时间线描述，如“过去3年我们…”，增强实战可信度。"

    def _expertise_suggestion(self, score: float) -> str:
        if score >= 3.2:
            return "专业性良好，保持术语/代码/步骤化呈现。"
        return "增加技术细节：代码示例、数据表或方法论步骤，体现专业深度。"

    def _authority_suggestion(self, score: float) -> str:
        if score >= 3.0:
            return "权威信号到位，继续引用官方或.gov/.edu来源。"
        return "完善作者简介并引用2-3个权威来源（官方文档/行业报告），提升权威度。"

    def _trust_suggestion(self, score: float) -> str:
        if score >= 2.5:
            return "可信度良好，保持日期与来源标注。"
        return "补充发布日期/更新日期，标注数据来源，必要时增加免责声明或联系信息。"
