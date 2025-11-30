"""
Schema Markup检测器 - 2025 SEO标准

核心职责:
- 从Markdown/HTML中提取JSON-LD代码块
- 验证Schema.org格式合法性
- 检查必填字段完整性（严格模式）

支持的Schema类型（覆盖90%博客场景）:
- Article/BlogPosting: 技术文章、博客
- FAQPage: FAQ章节
- HowTo: 教程指南
"""

import json
import re
from typing import List, Tuple, Dict, Optional, Any
from md_audit.models.data_models import DiagnosticItem, SeverityLevel


# 支持的Schema类型及其必填字段（2025标准）
SUPPORTED_SCHEMAS = {
    "Article": ["headline", "author", "datePublished"],
    "BlogPosting": ["headline", "author", "datePublished"],
    "FAQPage": ["mainEntity"],
    "HowTo": ["name", "step"],
}


class SchemaMarkupDetector:
    """Schema Markup检测器（2025 SEO标准）"""

    def __init__(self):
        # 预编译正则表达式（性能优化）
        self.json_ld_pattern = re.compile(
            r'<script\s+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            re.DOTALL | re.IGNORECASE,
        )
        self.markdown_json_block_pattern = re.compile(
            r"```json-?ld\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE
        )

    def detect(
        self,
        markdown_content: str,
        html_content: str,
        diagnostics: List[DiagnosticItem],
    ) -> float:
        """
        检测结构化数据并评分

        Args:
            markdown_content: Markdown原文（检查代码块中的JSON-LD）
            html_content: 渲染后的HTML（检查<script type="application/ld+json">）
            diagnostics: 诊断项列表（输出参数）

        Returns:
            得分（0-10分）

        评分逻辑:
        - 无Schema: 0分
        - 有Schema但格式错误: 3分
        - 格式正确但缺必填字段: 6分
        - Schema完整且格式正确: 10分
        """
        # 提取所有JSON-LD块
        schemas = self._extract_schemas(markdown_content, html_content)

        if not schemas:
            # 无Schema - 0分
            diagnostics.append(
                DiagnosticItem(
                    category="schema",
                    check_name="schema_markup_presence",
                    severity=SeverityLevel.WARNING,
                    score=0.0,
                    message="未检测到结构化数据（Schema Markup）",
                    suggestion=(
                        "添加JSON-LD结构化数据可提升Rich Results资格。"
                        "推荐类型: Article/BlogPosting（技术文章）、FAQPage（FAQ章节）、HowTo（教程）"
                    ),
                    current_value="无Schema",
                    expected_value="至少一个有效Schema（Article/BlogPosting/FAQPage/HowTo）",
                )
            )
            return 0.0

        # 验证每个Schema
        valid_schemas = []
        total_issues = []

        for idx, schema_data in enumerate(schemas):
            is_valid, schema_type, issues = self._validate_schema(schema_data)

            if is_valid and schema_type:
                valid_schemas.append(
                    {"type": schema_type, "data": schema_data, "issues": issues}
                )

            total_issues.extend(issues)

        # 计算得分
        if not valid_schemas:
            # 有Schema但全部格式错误 - 3分
            diagnostics.append(
                DiagnosticItem(
                    category="schema",
                    check_name="schema_markup_validity",
                    severity=SeverityLevel.CRITICAL,
                    score=3.0,
                    message=f"发现{len(schemas)}个Schema但格式无效",
                    suggestion=f"修复以下问题:\n"
                    + "\n".join(f"- {issue}" for issue in total_issues[:3]),
                    current_value=f"{len(schemas)}个无效Schema",
                    expected_value="有效的JSON-LD格式",
                )
            )
            return 3.0

        # 检查必填字段完整性
        complete_schemas = []
        missing_fields_issues = []

        for schema_info in valid_schemas:
            schema_type = schema_info["type"]
            schema_data = schema_info["data"]

            # 获取该类型的必填字段
            required_fields = SUPPORTED_SCHEMAS.get(schema_type, [])
            missing = [field for field in required_fields if field not in schema_data]

            if not missing:
                complete_schemas.append(schema_info)
            else:
                missing_fields_issues.append({"type": schema_type, "missing": missing})

        if not complete_schemas:
            # 格式正确但缺必填字段 - 6分
            issues_text = "\n".join(
                f"- {item['type']}: 缺少 {', '.join(item['missing'])}"
                for item in missing_fields_issues
            )
            diagnostics.append(
                DiagnosticItem(
                    category="schema",
                    check_name="schema_required_fields",
                    severity=SeverityLevel.CRITICAL,
                    score=6.0,
                    message=f"Schema缺少必填字段",
                    suggestion=(
                        f"补充以下必填字段:\n{issues_text}\n\n"
                        f"示例修复（Article类型）:\n"
                        f"{{\n"
                        f'  "@context": "https://schema.org",\n'
                        f'  "@type": "Article",\n'
                        f'  "headline": "文章标题",\n'
                        f'  "author": {{"@type": "Person", "name": "作者名"}},\n'
                        f'  "datePublished": "2025-01-01"\n'
                        f"}}"
                    ),
                    current_value=f"{len(valid_schemas)}个Schema缺少必填字段",
                    expected_value="所有必填字段完整",
                )
            )
            return 6.0

        # Schema完整且格式正确 - 10分
        schema_types = [s["type"] for s in complete_schemas]
        diagnostics.append(
            DiagnosticItem(
                category="schema",
                check_name="schema_markup_complete",
                severity=SeverityLevel.SUCCESS,
                score=10.0,
                message=f"结构化数据完整（{len(complete_schemas)}个有效Schema）",
                suggestion="",
                current_value=f"Schema类型: {', '.join(schema_types)}",
                expected_value="有效且完整的Schema",
            )
        )

        return 10.0

    def _extract_schemas(
        self, markdown_content: str, html_content: str
    ) -> List[Dict[str, Any]]:
        """
        从Markdown和HTML中提取所有JSON-LD代码块

        Returns:
            JSON-LD数据列表（已解析为dict）
        """
        schemas = []

        # 1. 从HTML中提取<script type="application/ld+json">
        html_matches = self.json_ld_pattern.findall(html_content)
        for json_str in html_matches:
            try:
                data = json.loads(json_str.strip())
                schemas.append(data)
            except json.JSONDecodeError:
                # 格式错误，跳过（后续验证会处理）
                pass

        # 2. 从Markdown代码块中提取```json-ld
        md_matches = self.markdown_json_block_pattern.findall(markdown_content)
        for json_str in md_matches:
            try:
                data = json.loads(json_str.strip())
                schemas.append(data)
            except json.JSONDecodeError:
                # 格式错误，跳过
                pass

        return schemas

    def _validate_schema(
        self, schema_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        验证单个Schema的格式和类型

        Returns:
            (是否有效, Schema类型, 问题列表)
        """
        issues = []

        # 检查@context字段
        context = schema_data.get("@context")
        if not context:
            issues.append("缺少@context字段")
            return False, None, issues

        if not isinstance(context, str) or "schema.org" not in context.lower():
            issues.append(f"@context必须为https://schema.org，当前为: {context}")
            return False, None, issues

        # 检查@type字段
        schema_type = schema_data.get("@type")
        if not schema_type:
            issues.append("缺少@type字段")
            return False, None, issues

        # 处理@type为数组的情况（如["Article", "BlogPosting"]）
        if isinstance(schema_type, list):
            # 验证所有类型是否都在支持列表中
            valid_types = [t for t in schema_type if t in SUPPORTED_SCHEMAS]
            if not valid_types:
                issues.append(
                    f"@type包含的类型均不支持: {schema_type}。"
                    f"支持的类型: {list(SUPPORTED_SCHEMAS.keys())}"
                )
                return False, None, issues
            # 使用第一个支持的类型
            schema_type = valid_types[0]

        # 检查类型是否支持
        if schema_type not in SUPPORTED_SCHEMAS:
            issues.append(
                f"不支持的Schema类型: {schema_type}。"
                f"当前仅支持: {list(SUPPORTED_SCHEMAS.keys())}"
            )
            return False, None, issues

        return True, schema_type, issues
