"""
规则检查引擎 - 2025 SEO Standards
基于 Ahrefs, SEMrush, Backlinko 权威标准 + 博客效果分析框架

评分体系（60分满分，配合AI的40分）：
- 元数据优化: 25分 (Title 15分 + Description 10分)
- 内容结构: 20分 (标题层级4分 + 图片Alt 6分 + 链接密度6分 + FAQ 4分)
- 主题相关性: 19分 (内容长度5分 + 关键词优化8分 + E-E-A-T 6分)
  * 关键词优化细分：覆盖率2分 + 密度2分 + H标签+实体2分 + 位置分布2分

2025 关键词评估标准：
- 密度检测：0.5%-2.5%为适中范围
- H标签检测：核心关键词、变体(Variants)、实体(Entities)需出现在H1/H2中
- 实体识别：从内容中提取命名实体（产品名、品牌名、专有名词）
- 变体检测：识别关键词的同义词、复数形式、相关术语
- 位置检测：Title/首段/尾段是关键位置
- 2025趋势：不追求堆砌密度，追求语义自然覆盖和实体关联

2025元数据标准：
- Title: 50-60字符（600px SERP限制）
- Description: 150-160字符桌面端，120字符移动端
- 内容长度: 1500-2500词（Backlinko研究：Top 10平均1447词）
- 内链密度: 3-5个/1000词
- E-E-A-T: 作者信息、发布日期、引用来源
"""

import re
from typing import List, Tuple, Dict, Any
from md_audit.models.data_models import ParsedMarkdown, DiagnosticItem, SeverityLevel
from md_audit.config import MarkdownSEOConfig


class RulesEngine:
    """规则检查引擎（2025 SEO Standards）"""

    def __init__(self, config: MarkdownSEOConfig):
        self.config = config

    # 新增公开方法，便于独立维度评分
    def run_metadata(self, parsed: ParsedMarkdown):
        diagnostics: List[DiagnosticItem] = []
        score = self._check_metadata(parsed, diagnostics)
        return score, diagnostics

    def run_structure(self, parsed: ParsedMarkdown):
        diagnostics: List[DiagnosticItem] = []
        score = self._check_structure(parsed, diagnostics)
        return score, diagnostics

    def run_keyword(self, parsed: ParsedMarkdown, keywords: List[str]):
        diagnostics: List[DiagnosticItem] = []
        score = self._check_keyword_coverage(parsed, keywords, diagnostics)
        return score, diagnostics

    def check_all(self, parsed: ParsedMarkdown, keywords: List[str]) -> Tuple[float, List[DiagnosticItem]]:
        """
        执行所有规则检查（2025 SEO Standards - 对标博客效果分析框架）

        评分维度（66分原始分，归一化到60分）：
        1. 元数据 (25分): Title15分 + Description10分 - 对标参考框架20分
        2. 内容结构 (22分): 标题层级6分 + 图片Alt5分 + 链接密度5分 + FAQ6分 - 对标参考框架25分
        3. 主题相关性 (19分): 内容长度5分 + 关键词优化8分 + E-E-A-T6分 - 对标参考框架30分

        关键词优化包含（对标参考框架"目标关键词与搜索意图"10分）：
        - 覆盖率（2分）
        - 密度检测（2分）：0.5%-2.5%为适中
        - H标签+实体+变体（2分）：核心关键词、Variants和Entities
        - 位置分布（2分）：Title/首段/尾段

        Returns:
            (总分（归一化到60分）, 诊断项列表)
        """
        diagnostics: List[DiagnosticItem] = []

        # 元数据检查（25分）- 2025标准
        metadata_score = self._check_metadata(parsed, diagnostics)

        # 结构检查（22分）- 标题层级6 + 图片Alt5 + 链接密度5 + FAQ6
        structure_score = self._check_structure(parsed, diagnostics)

        # 主题相关性+E-E-A-T检查（19分）
        relevance_score = self._check_topic_relevance(parsed, keywords, diagnostics)

        # 原始分数（最高66分）
        raw_score = metadata_score + structure_score + relevance_score

        # 归一化到60分满分 - 对标参考框架
        # 新分布：元数据25 + 结构22 + 相关性19 = 66
        max_raw_score = 66
        total_score = min(60, (raw_score / max_raw_score) * 60)

        return round(total_score, 1), diagnostics

    def _check_metadata(self, parsed: ParsedMarkdown, diagnostics: List[DiagnosticItem]) -> float:
        """
        检查元数据（2025 Standard）

        Title: 15分
        - 50-60字符最优（600px SERP显示限制）
        - 包含核心关键词
        - 前置关键词（Front-load）

        Description: 10分
        - 桌面端: 150-160字符
        - 移动端: 120字符
        - 包含CTA和关键词
        """
        score = 0.0

        # 标题检查（15分）- 2025标准：50-60字符
        title = parsed.title
        title_len = len(title)
        rules = self.config.title

        if not title:
            diagnostics.append(DiagnosticItem(
                category="metadata",
                check_name="title_exists",
                severity=SeverityLevel.CRITICAL,
                score=0,
                message="缺少标题（Title Tag）",
                suggestion="添加50-60字符的标题，前置核心关键词。2025 SERP最大显示宽度600px",
                current_value="无",
                expected_value="必须存在"
            ))
        elif title_len < rules.min_length:
            # 标题过短（<50字符）
            partial_score = 7
            diagnostics.append(DiagnosticItem(
                category="metadata",
                check_name="title_length",
                severity=SeverityLevel.WARNING,
                score=partial_score,
                message=f"标题过短（{title_len}字符）",
                suggestion=f"2025标准：50-60字符最优。过短的标题难以充分描述页面内容，影响点击率",
                current_value=str(title_len),
                expected_value=f"{rules.min_length}-{rules.max_length}"
            ))
            score += partial_score
        elif title_len > rules.max_length:
            # 标题过长（>60字符）会被SERP截断
            partial_score = 10
            diagnostics.append(DiagnosticItem(
                category="metadata",
                check_name="title_length",
                severity=SeverityLevel.INFO,
                score=partial_score,
                message=f"标题略长（{title_len}字符）",
                suggestion=f"超过{rules.max_length}字符会被Google截断（600px限制）。建议精简至50-60字符",
                current_value=str(title_len),
                expected_value=f"{rules.min_length}-{rules.max_length}"
            ))
            score += partial_score
        else:
            diagnostics.append(DiagnosticItem(
                category="metadata",
                check_name="title_length",
                severity=SeverityLevel.SUCCESS,
                score=15,
                message=f"标题长度最优（{title_len}字符）",
                current_value=str(title_len),
                expected_value=f"{rules.min_length}-{rules.max_length}"
            ))
            score += 15

        # 描述检查（10分）- 2025标准：150-160字符桌面/120移动
        desc = parsed.description
        desc_len = len(desc)
        desc_rules = self.config.description

        if not desc:
            diagnostics.append(DiagnosticItem(
                category="metadata",
                check_name="description_exists",
                severity=SeverityLevel.WARNING,
                score=0,
                message="缺少Meta Description",
                suggestion="添加150-160字符的描述。包含核心关键词和明确的价值主张（CTA）",
                current_value="无",
                expected_value="必须存在"
            ))
        elif desc_len < desc_rules.min_length:
            partial_score = 4
            diagnostics.append(DiagnosticItem(
                category="metadata",
                check_name="description_length",
                severity=SeverityLevel.WARNING,
                score=partial_score,
                message=f"描述过短（{desc_len}字符）",
                suggestion=f"2025标准：150-160字符（920px）。移动端建议120字符内。当前描述难以充分传达内容价值",
                current_value=str(desc_len),
                expected_value=f"{desc_rules.min_length}-{desc_rules.max_length}"
            ))
            score += partial_score
        elif desc_len > desc_rules.max_length:
            partial_score = 7
            diagnostics.append(DiagnosticItem(
                category="metadata",
                check_name="description_length",
                severity=SeverityLevel.INFO,
                score=partial_score,
                message=f"描述略长（{desc_len}字符）",
                suggestion=f"超过{desc_rules.max_length}字符会被截断。移动端仅显示约120字符，确保关键信息在前半部分",
                current_value=str(desc_len),
                expected_value=f"{desc_rules.min_length}-{desc_rules.max_length}"
            ))
            score += partial_score
        else:
            diagnostics.append(DiagnosticItem(
                category="metadata",
                check_name="description_length",
                severity=SeverityLevel.SUCCESS,
                score=10,
                message=f"描述长度合适（{desc_len}字符）",
                current_value=str(desc_len),
                expected_value=f"{desc_rules.min_length}-{desc_rules.max_length}"
            ))
            score += 10

        return score

    def _check_structure(self, parsed: ParsedMarkdown, diagnostics: List[DiagnosticItem]) -> float:
        """
        检查内容结构（2025 Standard）

        评分分布（22分）- 对标参考框架"页面优化"：
        - 标题层级: 6分（H1唯一性 + H2数量 + 层级规范）- 参考框架10分
        - 图片Alt: 5分（80%覆盖率 + Alt长度）- 参考框架5分
        - 链接密度: 5分（3-5个内链/1000词）- 参考框架5分
        - FAQ/结构化内容: 6分（AI搜索优化）
        """
        score = 0.0
        word_count = parsed.word_count

        # 标题层级检查（6分）- H1唯一性 + 足够的H2 + 层级规范
        h1_count = len(parsed.h1_tags)
        h2_count = len(parsed.h2_tags) if hasattr(parsed, 'h2_tags') else 0
        min_h2 = self.config.content.min_h2_count  # 2025标准：至少3个H2

        heading_score = 0
        heading_issues = []

        # H1检查：必须唯一（3分）
        if h1_count == 1:
            heading_score += 3
        elif h1_count == 0:
            heading_issues.append("缺少H1标题")
        else:
            heading_issues.append(f"存在{h1_count}个H1，应保持唯一")
            heading_score += 1

        # H2检查：至少3个以构建清晰结构（3分）
        if h2_count >= min_h2:
            heading_score += 3
        elif h2_count >= 1:
            heading_issues.append(f"H2数量不足（{h2_count}/{min_h2}）")
            heading_score += 1.5
        else:
            heading_issues.append("缺少H2章节标题")

        if heading_score == 6:
            diagnostics.append(DiagnosticItem(
                category="structure",
                check_name="heading_hierarchy",
                severity=SeverityLevel.SUCCESS,
                score=6,
                message=f"标题层级规范（H1:{h1_count}, H2:{h2_count}）",
                current_value=f"H1:{h1_count}, H2:{h2_count}"
            ))
        else:
            diagnostics.append(DiagnosticItem(
                category="structure",
                check_name="heading_hierarchy",
                severity=SeverityLevel.WARNING if heading_score < 3 else SeverityLevel.INFO,
                score=heading_score,
                message="标题结构需优化",
                suggestion=f"问题：{'; '.join(heading_issues)}。2025标准：1个H1 + 至少{min_h2}个H2构建清晰内容结构",
                current_value=f"H1:{h1_count}, H2:{h2_count}",
                expected_value=f"H1:1, H2:>={min_h2}"
            ))
        score += heading_score

        # 图片Alt检查（5分）- 80%覆盖率 + Alt文本质量 - 对标参考框架5分
        total_images = len(parsed.images)
        images_with_alt = sum(1 for img in parsed.images if img.get('alt'))
        alt_ratio = images_with_alt / total_images if total_images > 0 else 1.0

        if total_images == 0:
            diagnostics.append(DiagnosticItem(
                category="structure",
                check_name="image_alt",
                severity=SeverityLevel.INFO,
                score=3,
                message="文章无图片",
                suggestion="添加相关图片可提升用户体验和内容丰富度。图片Alt文本建议80-125字符，描述性强"
            ))
            score += 3
        elif alt_ratio >= 0.8:
            diagnostics.append(DiagnosticItem(
                category="structure",
                check_name="image_alt",
                severity=SeverityLevel.SUCCESS,
                score=5,
                message=f"图片Alt覆盖良好（{images_with_alt}/{total_images}，{alt_ratio:.0%}）",
                current_value=f"{alt_ratio:.0%}"
            ))
            score += 5
        else:
            alt_score = round(5 * alt_ratio, 1)
            diagnostics.append(DiagnosticItem(
                category="structure",
                check_name="image_alt",
                severity=SeverityLevel.WARNING,
                score=alt_score,
                message=f"图片Alt覆盖不足（{images_with_alt}/{total_images}）",
                suggestion=f"2025标准：至少80%图片需要Alt文本。Alt应描述图片内容（80-125字符），包含相关关键词",
                current_value=f"{alt_ratio:.0%}",
                expected_value=">=80%"
            ))
            score += alt_score

        # 链接密度检查（5分）- 2025标准：3-5个内链/1000词 - 对标参考框架5分
        link_score = self._check_link_density(parsed, diagnostics, word_count)
        score += link_score

        # FAQ/结构化内容检查（6分）- AI搜索优化
        faq_score = self._check_structured_content(parsed, diagnostics)
        score += faq_score

        return score

    def _check_link_density(self, parsed: ParsedMarkdown, diagnostics: List[DiagnosticItem], word_count: int) -> float:
        """
        检查链接密度（2025 Standard）- 对标参考框架5分

        2025标准（Rush Analytics, Zyppy研究）：
        - 内链：3-5个/1000词
        - 外链：至少1个权威引用
        - 总链接：不超过150个/页面
        """
        link_rules = self.config.links
        total_links = len(parsed.links)

        # 分类链接
        internal_links = []
        external_links = []
        for link in parsed.links:
            href = link.get('href', '')
            if href.startswith(('http://', 'https://')):
                external_links.append(link)
            elif href.startswith(('//', 'mailto:', 'tel:')):
                pass  # 忽略
            else:
                internal_links.append(link)

        internal_count = len(internal_links)
        external_count = len(external_links)

        # 计算链接密度（每1000词）
        words_in_k = word_count / 1000 if word_count > 0 else 1
        internal_density = internal_count / words_in_k

        # 评分逻辑（5分）- 对标参考框架
        link_score = 0

        # 内链密度检查（3分）
        optimal_min = link_rules.optimal_internal_links_per_1000_words  # 3
        optimal_max = link_rules.max_internal_links_per_1000_words  # 5

        if optimal_min <= internal_density <= optimal_max:
            link_score += 3
            link_msg = f"内链密度最优（{internal_density:.1f}个/千词）"
            link_severity = SeverityLevel.SUCCESS
        elif internal_density < optimal_min:
            if internal_density >= 1:
                link_score += 1.5
                link_msg = f"内链偏少（{internal_density:.1f}个/千词）"
            else:
                link_msg = f"内链严重不足（{internal_density:.1f}个/千词）"
            link_severity = SeverityLevel.WARNING
        else:
            # 过多内链
            link_score += 1.5
            link_msg = f"内链过多（{internal_density:.1f}个/千词）"
            link_severity = SeverityLevel.INFO

        # 外链检查（2分）
        if external_count >= link_rules.min_external_links:
            link_score += 2
            ext_msg = f"有{external_count}个外部引用"
        else:
            ext_msg = "缺少外部权威引用"

        # 总链接数检查
        if total_links > link_rules.max_total_links:
            link_score = max(0, link_score - 1)
            link_severity = SeverityLevel.WARNING

        diagnostics.append(DiagnosticItem(
            category="structure",
            check_name="link_density",
            severity=link_severity,
            score=link_score,
            message=f"{link_msg}，{ext_msg}",
            suggestion=f"2025标准：内链3-5个/千词，至少1个外部权威引用。当前：内链{internal_count}，外链{external_count}，总计{total_links}",
            current_value=f"内链:{internal_count}, 外链:{external_count}",
            expected_value=f"内链密度:{optimal_min}-{optimal_max}/千词"
        ))

        return link_score

    def _check_structured_content(self, parsed: ParsedMarkdown, diagnostics: List[DiagnosticItem]) -> float:
        """
        检查FAQ和结构化内容（2025 AI搜索优化）- 6分

        2025趋势（Ahrefs 82-Point Checklist）：
        - FAQ章节有助于AI Overview展示（3分）
        - 列表内容（有序/无序）提升可读性（1.5分）
        - 清晰的问答格式利于Featured Snippets（1.5分）
        """
        ai_rules = self.config.ai_search
        content = parsed.raw_content.lower()
        struct_score = 0

        # 检测FAQ章节（3分）
        has_faq = False
        faq_patterns = [
            r'##\s*(faq|常见问题|frequently\s*asked)',
            r'\?\s*\n+[-*]',  # 问题后跟列表
            r'###\s*.+\?',    # H3问题格式
        ]
        for pattern in faq_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                has_faq = True
                break

        if has_faq:
            struct_score += 3

        # 检测列表内容（1.5分）
        list_patterns = [
            r'^[-*+]\s+',     # 无序列表
            r'^\d+\.\s+',     # 有序列表
        ]
        has_lists = any(re.search(p, parsed.raw_content, re.MULTILINE) for p in list_patterns)
        if has_lists:
            struct_score += 1.5

        # 检测结构化答案（1.5分）- 直接回答格式
        answer_patterns = [
            r'(简单来说|简而言之|总结|答案是|结论)',
            r'(in short|in summary|the answer is|to summarize)',
        ]
        has_structured_answer = any(re.search(p, content) for p in answer_patterns)
        if has_structured_answer:
            struct_score += 1.5

        # 生成诊断信息
        findings = []
        if has_faq:
            findings.append("包含FAQ章节")
        if has_lists:
            findings.append("使用列表结构")
        if has_structured_answer:
            findings.append("有结构化答案")

        if struct_score >= 4.5:
            diagnostics.append(DiagnosticItem(
                category="structure",
                check_name="structured_content",
                severity=SeverityLevel.SUCCESS,
                score=6,
                message=f"AI搜索优化良好（{', '.join(findings)}）",
                current_value=f"{struct_score}/6"
            ))
            return 6
        elif struct_score > 0:
            diagnostics.append(DiagnosticItem(
                category="structure",
                check_name="structured_content",
                severity=SeverityLevel.INFO,
                score=struct_score,
                message=f"部分AI搜索优化（{', '.join(findings) if findings else '基础结构'}）",
                suggestion="2025趋势：添加FAQ章节、使用列表、提供简洁直接的答案，有助于被AI Overview和Featured Snippets展示",
                current_value=f"{struct_score}/6"
            ))
            return struct_score
        else:
            diagnostics.append(DiagnosticItem(
                category="structure",
                check_name="structured_content",
                severity=SeverityLevel.INFO,
                score=0,
                message="未检测到AI搜索优化结构",
                suggestion="建议添加：1) FAQ章节回答常见问题 2) 使用列表组织要点 3) 在关键位置提供简洁直接的答案"
            ))
            return 0

    def _check_topic_relevance(self, parsed: ParsedMarkdown, keywords: List[str], diagnostics: List[DiagnosticItem]) -> float:
        """
        检查主题相关性和E-E-A-T信号（2025 Standard）

        评分分布（19分）：
        - 内容长度: 5分（2025标准：1500-2500词）
        - 关键词优化: 8分（覆盖+密度+H标签+位置）
        - E-E-A-T信号: 6分（作者信息、发布日期、引用）
        """
        score = 0.0
        word_count = parsed.word_count

        # 内容长度检查（5分）- 2025标准：1500-2500词最优
        min_length = self.config.content.min_length  # 1500
        optimal_length = self.config.content.optimal_length  # 2000
        max_length = self.config.content.max_length  # 3500

        if optimal_length <= word_count <= max_length:
            diagnostics.append(DiagnosticItem(
                category="relevance",
                check_name="content_length",
                severity=SeverityLevel.SUCCESS,
                score=5,
                message=f"内容长度最优（{word_count}词）",
                suggestion="内容深度适合深入覆盖主题，符合Backlinko研究的Top 10平均长度",
                current_value=str(word_count),
                expected_value=f"{optimal_length}-{max_length}"
            ))
            score += 5
        elif min_length <= word_count < optimal_length:
            diagnostics.append(DiagnosticItem(
                category="relevance",
                check_name="content_length",
                severity=SeverityLevel.INFO,
                score=4,
                message=f"内容长度合格（{word_count}词）",
                suggestion=f"达到最低要求，建议扩展至{optimal_length}词以提升主题覆盖深度",
                current_value=str(word_count),
                expected_value=f"{optimal_length}-{max_length}"
            ))
            score += 4
        elif word_count > max_length:
            diagnostics.append(DiagnosticItem(
                category="relevance",
                check_name="content_length",
                severity=SeverityLevel.INFO,
                score=4,
                message=f"内容较长（{word_count}词）",
                suggestion="内容较长，确保每个章节都有实质价值，避免注水",
                current_value=str(word_count)
            ))
            score += 4
        elif word_count >= min_length * 0.5:  # 750词
            partial = 2
            diagnostics.append(DiagnosticItem(
                category="relevance",
                check_name="content_length",
                severity=SeverityLevel.WARNING,
                score=partial,
                message=f"内容偏短（{word_count}词）",
                suggestion=f"2025标准：{min_length}词起步，{optimal_length}词最优。Backlinko研究显示Top 10平均1447词",
                current_value=str(word_count),
                expected_value=f">={min_length}"
            ))
            score += partial
        else:
            diagnostics.append(DiagnosticItem(
                category="relevance",
                check_name="content_length",
                severity=SeverityLevel.CRITICAL,
                score=0,
                message=f"内容严重不足（{word_count}词）",
                suggestion=f"内容过短难以建立主题权威性。2025 SEO要求至少{min_length}词以深入覆盖主题",
                current_value=str(word_count),
                expected_value=f">={min_length}"
            ))

        # 关键词优化检查（8分）- 包含覆盖、密度、H标签、位置
        keyword_score = self._check_keyword_coverage(parsed, keywords, diagnostics)
        score += keyword_score

        # E-E-A-T信号检查（6分）
        eeat_score = self._check_eeat_signals(parsed, diagnostics)
        score += eeat_score

        return score

    def _check_keyword_coverage(self, parsed: ParsedMarkdown, keywords: List[str], diagnostics: List[DiagnosticItem]) -> float:
        """
        检查关键词覆盖、密度和位置分布（2025 Standard）

        评分分布（8分）：
        - 关键词覆盖: 2分
        - 关键词密度: 2分（0.5%-2.5%适中）
        - H标签关键词: 2分
        - 位置分布: 2分（Title/首段/尾段）
        """
        content = parsed.raw_content.lower()
        word_count = parsed.word_count

        if not keywords:
            diagnostics.append(DiagnosticItem(
                category="relevance",
                check_name="keyword_coverage",
                severity=SeverityLevel.INFO,
                score=4,
                message="未指定目标关键词，跳过关键词检查"
            ))
            return 4

        total_score = 0.0

        # 1. 关键词覆盖率检查（2分）
        keywords_found = [kw for kw in keywords if kw.lower() in content]
        coverage = len(keywords_found) / len(keywords) if keywords else 0

        if coverage >= 0.6:
            total_score += 2
        elif coverage > 0:
            total_score += 1

        # 2. 关键词密度检查（2分）- 0.5%-2.5%为适中范围
        density_score, density_details = self._calculate_keyword_density(content, keywords, word_count)
        total_score += density_score

        # 3. H标签关键词检查（2分）
        h_tag_score, h_tag_details = self._check_keywords_in_headings(parsed, keywords)
        total_score += h_tag_score

        # 4. 位置分布检查（2分）- Title/首段/尾段
        position_score, position_details = self._check_keyword_positions(parsed, keywords, content)
        total_score += position_score

        # 生成综合诊断信息
        all_details = []
        all_details.append(f"覆盖率: {coverage:.0%} ({len(keywords_found)}/{len(keywords)})")
        all_details.append(density_details)
        all_details.append(h_tag_details)
        all_details.append(position_details)

        if total_score >= 6:
            diagnostics.append(DiagnosticItem(
                category="relevance",
                check_name="keyword_coverage",
                severity=SeverityLevel.SUCCESS,
                score=total_score,
                message=f"关键词优化良好",
                suggestion=" | ".join(all_details),
                current_value=", ".join(keywords_found[:5])
            ))
        elif total_score >= 3:
            diagnostics.append(DiagnosticItem(
                category="relevance",
                check_name="keyword_coverage",
                severity=SeverityLevel.INFO,
                score=total_score,
                message="关键词优化需改进",
                suggestion=" | ".join(all_details),
                current_value=", ".join(keywords_found[:5])
            ))
        else:
            diagnostics.append(DiagnosticItem(
                category="relevance",
                check_name="keyword_coverage",
                severity=SeverityLevel.WARNING,
                score=total_score,
                message="关键词优化不足",
                suggestion=" | ".join(all_details) + " | 建议在H2标题中包含核心关键词及其变体"
            ))

        return total_score

    def _calculate_keyword_density(self, content: str, keywords: List[str], word_count: int) -> Tuple[float, str]:
        """
        计算关键词密度

        2025标准：0.5%-2.5%为适中范围
        <0.5% 密度过低
        >2.5% 可能过度优化（keyword stuffing）
        """
        if word_count == 0:
            return 0, "密度: N/A (无内容)"

        total_keyword_count = 0
        density_details = []

        for kw in keywords:
            kw_lower = kw.lower()
            # 计算关键词出现次数
            count = content.count(kw_lower)
            total_keyword_count += count
            if count > 0:
                kw_density = (count * len(kw_lower.split())) / word_count * 100
                density_details.append(f"{kw}:{count}次({kw_density:.1f}%)")

        # 计算综合密度
        avg_density = total_keyword_count / word_count * 100 if word_count > 0 else 0

        # 评分（2分）
        if 0.5 <= avg_density <= 2.5:
            score = 2
            status = "适中"
        elif 0.3 <= avg_density < 0.5:
            score = 1
            status = "偏低"
        elif 2.5 < avg_density <= 3.5:
            score = 1
            status = "偏高"
        elif avg_density < 0.3:
            score = 0
            status = "过低"
        else:
            score = 0
            status = "过度优化风险"

        detail_str = f"密度: {avg_density:.2f}% ({status})"
        if density_details:
            detail_str += f" [{', '.join(density_details[:3])}]"

        return score, detail_str

    def _check_keywords_in_headings(self, parsed: ParsedMarkdown, keywords: List[str]) -> Tuple[float, str]:
        """
        检查关键词、变体(Variants)和实体(Entities)在H标签中的出现

        参考框架要求：H标题中需要包含核心关键词、Variants和entities
        """
        h1_keywords = []
        h2_keywords = []
        h_variants = []
        h_entities = []

        h1_tags = parsed.h1_tags
        h2_tags = parsed.h2_tags if hasattr(parsed, 'h2_tags') else []

        # 合并所有H标签文本
        h1_text = " ".join(h1_tags).lower()
        h2_text = " ".join(h2_tags).lower()
        all_h_text = h1_text + " " + h2_text

        # 1. 检查关键词
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in h1_text:
                h1_keywords.append(kw)
            if kw_lower in h2_text:
                h2_keywords.append(kw)

        # 2. 提取并检查变体(Variants)
        variants = self._extract_keyword_variants(keywords)
        for var in variants:
            if var.lower() in all_h_text:
                h_variants.append(var)

        # 3. 从内容中提取实体并检查H标签
        entities = self._extract_entities(parsed.raw_content)
        for entity in entities[:10]:  # 限制检查前10个实体
            if entity.lower() in all_h_text:
                h_entities.append(entity)

        # 评分（2分）- 关键词0.5 + 变体0.5 + 实体1
        score = 0
        if h1_keywords or h2_keywords:
            score += 0.5
        if h_variants:
            score += 0.5
        if h_entities:
            score += 1

        # 兜底：如果至少有关键词命中，保证最低1分
        if (h1_keywords or h2_keywords) and score < 1:
            score = 1

        # 详情
        details = []
        if h1_keywords:
            details.append(f"H1:{','.join(h1_keywords[:2])}")
        if h2_keywords:
            details.append(f"H2:{','.join(h2_keywords[:3])}")
        if h_variants:
            details.append(f"变体:{','.join(h_variants[:2])}")
        if h_entities:
            details.append(f"实体:{','.join(h_entities[:2])}")

        if not details:
            details.append("H标签无关键词/变体/实体")

        return score, "H标签+实体: " + ", ".join(details)

    def _extract_keyword_variants(self, keywords: List[str]) -> List[str]:
        """
        提取关键词变体(Variants)

        变体包括：
        - 复数/单数形式
        - 动词形式变化（ing, ed, s）
        - 常见同义词和相关术语
        """
        variants = []

        for kw in keywords:
            kw_lower = kw.lower().strip()
            if not kw_lower:
                continue

            # 英文变体
            if kw_lower.isascii():
                # 复数形式
                if not kw_lower.endswith('s'):
                    variants.append(kw_lower + 's')
                    variants.append(kw_lower + 'es')
                else:
                    # 去掉s得到单数
                    variants.append(kw_lower[:-1])

                # 动词变形
                if not kw_lower.endswith('ing'):
                    variants.append(kw_lower + 'ing')
                if not kw_lower.endswith('ed'):
                    variants.append(kw_lower + 'ed')
                if not kw_lower.endswith('er'):
                    variants.append(kw_lower + 'er')

                # 常见前缀变体
                variants.append('best ' + kw_lower)
                variants.append('top ' + kw_lower)
                variants.append(kw_lower + ' guide')
                variants.append(kw_lower + ' tips')
                variants.append('how to ' + kw_lower)

        # 去重并限制数量
        seen = set()
        unique_variants = []
        for v in variants:
            v_clean = v.lower().strip()
            if v_clean not in seen and v_clean not in [k.lower() for k in keywords]:
                seen.add(v_clean)
                unique_variants.append(v)

        return unique_variants[:20]  # 限制最多20个变体

    def _extract_entities(self, content: str) -> List[str]:
        """
        从内容中提取命名实体(Entities)

        实体类型：
        - 产品名/品牌名（大写开头的连续词）
        - 专有名词
        - 技术术语
        - 引号内的术语
        """
        entities = []

        # 1. 提取引号内的术语（通常是专有名词或重要术语）
        quoted_patterns = [
            r'"([^"]{2,30})"',
            r"'([^']{2,30})'",
            r'"([^"]{2,30})"',
            r'「([^」]{2,30})」',
            r'【([^】]{2,30})】',
        ]
        for pattern in quoted_patterns:
            matches = re.findall(pattern, content)
            entities.extend(matches)

        # 2. 提取大写开头的专有名词（英文品牌名、产品名）
        # 匹配连续的大写开头单词（如 "Google Analytics", "Meta Description"）
        proper_noun_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        proper_nouns = re.findall(proper_noun_pattern, content)

        # 过滤常见的非实体词
        common_words = {
            'The', 'This', 'That', 'These', 'Those', 'Here', 'There',
            'What', 'When', 'Where', 'Why', 'How', 'Which', 'Who',
            'First', 'Second', 'Third', 'Next', 'Last', 'Final',
            'Table', 'Figure', 'Image', 'Chapter', 'Section', 'Part',
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December',
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
        }
        for noun in proper_nouns:
            if noun not in common_words and len(noun) >= 3:
                entities.append(noun)

        # 3. 提取技术术语（全大写缩写，如SEO, API, HTML）
        acronym_pattern = r'\b([A-Z]{2,6})\b'
        acronyms = re.findall(acronym_pattern, content)
        # 过滤常见非术语缩写
        common_acronyms = {'OK', 'OR', 'AND', 'NOT', 'THE', 'FOR', 'BUT', 'SO', 'IF'}
        for acr in acronyms:
            if acr not in common_acronyms:
                entities.append(acr)

        # 4. 提取中文专有名词（连续的中文词+数字组合）
        chinese_entity_pattern = r'[\u4e00-\u9fa5]{2,8}(?:\d+(?:\.\d+)?)?'
        chinese_entities = re.findall(chinese_entity_pattern, content)
        # 过滤太常见的词
        for ce in chinese_entities:
            if len(ce) >= 3 and not self._is_common_chinese_word(ce):
                entities.append(ce)

        # 去重并按出现频率排序
        entity_count = {}
        for e in entities:
            e_lower = e.lower() if e.isascii() else e
            entity_count[e_lower] = entity_count.get(e_lower, 0) + 1

        # 按频率排序，返回最常出现的实体
        sorted_entities = sorted(entity_count.keys(), key=lambda x: entity_count[x], reverse=True)

        return sorted_entities[:15]  # 返回前15个最重要的实体

    def _is_common_chinese_word(self, word: str) -> bool:
        """判断是否为常见中文词（非实体）"""
        common_words = {
            '的', '是', '在', '有', '和', '与', '或', '但', '因为', '所以',
            '这个', '那个', '如果', '可以', '需要', '应该', '可能', '已经',
            '文章', '内容', '页面', '网站', '用户', '我们', '他们', '这些',
            '一个', '两个', '一些', '很多', '所有', '每个', '任何', '其他',
            '非常', '比较', '更加', '最好', '更好', '最佳', '最优',
        }
        return word in common_words

    def _check_keyword_positions(self, parsed: ParsedMarkdown, keywords: List[str], content: str) -> Tuple[float, str]:
        """
        检查关键词位置分布

        重要位置：Title, 首段(前200字), 尾段(后200字)
        """
        title = parsed.title.lower()
        first_para = content[:500]
        last_para = content[-500:] if len(content) > 500 else content

        title_kw = [kw for kw in keywords if kw.lower() in title]
        first_kw = [kw for kw in keywords if kw.lower() in first_para]
        last_kw = [kw for kw in keywords if kw.lower() in last_para]

        # 评分（2分）
        score = 0
        positions = []

        if title_kw:
            score += 1
            positions.append("Title")
        if first_kw:
            score += 0.5
            positions.append("首段")
        if last_kw:
            score += 0.5
            positions.append("尾段")

        score = min(2, score)  # 最高2分

        if positions:
            return score, f"位置: {'+'.join(positions)}"
        else:
            return 0, "位置: 未在关键位置出现"

    def _check_eeat_signals(self, parsed: ParsedMarkdown, diagnostics: List[DiagnosticItem]) -> float:
        """
        检查E-E-A-T信号（2025 Google Standard）

        E-E-A-T = Experience, Expertise, Authoritativeness, Trustworthiness

        检查项（6分）：
        - 作者信息: 1.5分
        - 发布/更新日期: 1.5分
        - 引用/来源: 3分
        """
        eeat_rules = self.config.eeat
        eeat_score = 0.0
        signals_found = []
        signals_missing = []

        # 检查作者信息（1.5分）
        author = parsed.frontmatter.get('author', '')
        if author:
            eeat_score += 1.5
            signals_found.append("作者信息")
        else:
            # 在内容中查找作者署名
            author_patterns = [
                r'(作者|author|by|written by)[：:\s]+[\w\u4e00-\u9fa5]+',
                r'(关于作者|about the author)',
            ]
            has_author = any(re.search(p, parsed.raw_content, re.IGNORECASE) for p in author_patterns)
            if has_author:
                eeat_score += 1.5
                signals_found.append("作者署名")
            else:
                signals_missing.append("作者信息")

        # 检查发布日期（1.5分）
        date_fields = ['date', 'published', 'created', 'updated', 'lastmod']
        has_date = any(parsed.frontmatter.get(f) for f in date_fields)
        if has_date:
            eeat_score += 1.5
            signals_found.append("发布日期")
        else:
            # 在内容中查找日期
            date_patterns = [
                r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}',
                r'(发布于|published|last updated)',
            ]
            has_date = any(re.search(p, parsed.raw_content, re.IGNORECASE) for p in date_patterns)
            if has_date:
                eeat_score += 1.5
                signals_found.append("日期标注")
            else:
                signals_missing.append("发布日期")

        # 检查引用/来源（3分）
        citation_score = 0.0
        content = parsed.raw_content

        # 检查引用模式
        citation_patterns = [
            r'(根据|according to|研究表明|study shows|source:|来源：)',
            r'\[\d+\]',  # 脚注引用 [1]
            r'\[.+\]\(.+\)',  # Markdown链接引用
            r'(参考文献|references|bibliography)',
        ]

        citations_found = sum(1 for p in citation_patterns if re.search(p, content, re.IGNORECASE))

        # 检查外部链接作为引用
        external_links = [l for l in parsed.links if l.get('href', '').startswith(('http://', 'https://'))]

        if citations_found >= 2 or len(external_links) >= eeat_rules.min_citations:
            citation_score = 3
            signals_found.append(f"引用来源({citations_found}处引用, {len(external_links)}个外链)")
        elif citations_found >= 1 or len(external_links) >= 1:
            citation_score = 1.5
            signals_found.append("部分引用")
        else:
            signals_missing.append("引用来源")

        eeat_score += citation_score

        # 生成诊断信息
        if eeat_score >= 4.5:
            diagnostics.append(DiagnosticItem(
                category="relevance",
                check_name="eeat_signals",
                severity=SeverityLevel.SUCCESS,
                score=eeat_score,
                message=f"E-E-A-T信号良好（{', '.join(signals_found)}）",
                current_value=f"{eeat_score}/6"
            ))
        elif eeat_score > 0:
            diagnostics.append(DiagnosticItem(
                category="relevance",
                check_name="eeat_signals",
                severity=SeverityLevel.INFO,
                score=eeat_score,
                message=f"E-E-A-T信号部分满足（{', '.join(signals_found)}）",
                suggestion=f"缺少：{', '.join(signals_missing)}。2025 Google E-E-A-T标准强调：作者专业背景、内容时效性、权威引用",
                current_value=f"{eeat_score}/6"
            ))
        else:
            diagnostics.append(DiagnosticItem(
                category="relevance",
                check_name="eeat_signals",
                severity=SeverityLevel.WARNING,
                score=0,
                message="缺乏E-E-A-T信号",
                suggestion="2025 Google E-E-A-T是核心排名因素。建议添加：1) 作者信息/简介 2) 发布/更新日期 3) 引用权威来源"
            ))

        return eeat_score
