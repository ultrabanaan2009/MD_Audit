"""
Core Web Vitals分析器 - 2025 SEO标准

核心职责:
- 调用Lighthouse CLI评估页面性能
- 解析JSON结果并计算Core Web Vitals得分
- 提供降级策略确保系统鲁棒性

性能指标（2025 Google标准）:
- LCP (Largest Contentful Paint): <2.5s (满分)
- FID (First Input Delay): <100ms (满分)
- CLS (Cumulative Layout Shift): <0.1 (满分)
"""

import subprocess
import json
import shutil
from typing import Optional, Dict, Any, List
from md_audit.models.data_models import DiagnosticItem, SeverityLevel


class CoreWebVitalsAnalyzer:
    """Core Web Vitals分析器（基于Lighthouse CLI）"""

    def __init__(self, lighthouse_path: str = "lighthouse"):
        """
        初始化CWV分析器

        Args:
            lighthouse_path: Lighthouse CLI路径（默认从PATH查找）
        """
        self.lighthouse_path = lighthouse_path
        self.timeout = 60  # Lighthouse执行超时（秒）

        # 检查Lighthouse是否可用
        if not self._check_lighthouse_available():
            raise RuntimeError(
                "Lighthouse未安装或不可用。" "请运行: npm install -g lighthouse"
            )

    def analyze(self, url: str, diagnostics: List[DiagnosticItem]) -> float:
        """
        执行Core Web Vitals评估

        Args:
            url: 目标URL（必须是可访问的HTTP/HTTPS地址）
            diagnostics: 诊断项列表（输出参数）

        Returns:
            得分（0-15分）

        评分分布:
        - LCP: 5分（<2.5s满分，>4s零分）
        - FID: 5分（<100ms满分，>300ms零分）
        - CLS: 5分（<0.1满分，>0.25零分）

        降级策略:
        - Lighthouse执行失败: 返回0分，记录WARNING
        - 超时: 返回0分，记录WARNING
        - URL不可访问: 返回0分，记录WARNING
        """
        try:
            # 运行Lighthouse
            result = self._run_lighthouse(url)

            if not result:
                # 执行失败，降级
                diagnostics.append(
                    DiagnosticItem(
                        category="core_web_vitals",
                        check_name="cwv_execution_failed",
                        severity=SeverityLevel.WARNING,
                        score=0.0,
                        message="Core Web Vitals评估失败（Lighthouse执行错误）",
                        suggestion=(
                            "可能原因:\n"
                            "- URL无法访问\n"
                            "- 网络超时\n"
                            "- Chrome无法启动\n"
                            "请检查URL有效性或稍后重试"
                        ),
                        current_value="评估失败",
                        expected_value="成功获取CWV数据",
                    )
                )
                return 0.0

            # 解析Lighthouse结果
            lcp_score, lcp_value = self._calculate_lcp_score(result)
            fid_score, fid_value = self._calculate_fid_score(result)
            cls_score, cls_value = self._calculate_cls_score(result)

            total_cwv_score = lcp_score + fid_score + cls_score

            # 添加诊断项
            self._add_cwv_diagnostics(
                diagnostics,
                lcp_score,
                lcp_value,
                fid_score,
                fid_value,
                cls_score,
                cls_value,
            )

            return round(total_cwv_score, 1)

        except subprocess.TimeoutExpired:
            # 超时降级
            diagnostics.append(
                DiagnosticItem(
                    category="core_web_vitals",
                    check_name="cwv_timeout",
                    severity=SeverityLevel.WARNING,
                    score=0.0,
                    message=f"Core Web Vitals评估超时（>{self.timeout}秒）",
                    suggestion="URL可能响应过慢，建议优化服务器性能或稍后重试",
                    current_value="超时",
                    expected_value="<60秒",
                )
            )
            return 0.0

        except Exception as e:
            # 其他异常降级
            diagnostics.append(
                DiagnosticItem(
                    category="core_web_vitals",
                    check_name="cwv_error",
                    severity=SeverityLevel.WARNING,
                    score=0.0,
                    message=f"Core Web Vitals评估异常: {str(e)}",
                    suggestion="请检查Lighthouse安装和URL有效性",
                    current_value="异常",
                    expected_value="正常执行",
                )
            )
            return 0.0

    def _check_lighthouse_available(self) -> bool:
        """检查Lighthouse CLI是否可用"""
        try:
            # 使用shutil.which更可靠地检查命令存在性
            lighthouse_cmd = shutil.which(self.lighthouse_path)
            if not lighthouse_cmd:
                return False

            # 验证版本（确保真的可执行）
            result = subprocess.run(
                [self.lighthouse_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0

        except Exception:
            return False

    def _run_lighthouse(self, url: str) -> Optional[Dict[str, Any]]:
        """
        运行Lighthouse CLI并返回JSON结果

        Args:
            url: 目标URL

        Returns:
            Lighthouse结果（dict），失败返回None
        """
        # 构造命令（安全参数列表，防止命令注入）
        cmd = [
            self.lighthouse_path,
            url,
            "--output=json",
            "--output-path=stdout",
            "--quiet",
            "--chrome-flags=--headless --no-sandbox",
            "--only-categories=performance",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                shell=False,  # 安全：禁用shell执行
            )

            if result.returncode != 0:
                # Lighthouse执行失败
                return None

            # 解析JSON输出
            data = json.loads(result.stdout)
            return data

        except json.JSONDecodeError:
            # JSON解析失败
            return None

        except Exception:
            # 其他错误
            return None

    def _calculate_lcp_score(
        self, lighthouse_result: Dict[str, Any]
    ) -> tuple[float, Optional[float]]:
        """
        计算LCP得分

        2025标准:
        - <2.5s: 5分（满分）
        - 2.5-4.0s: 2.5分（需改进）
        - >4.0s: 0分（差）

        Returns:
            (得分, LCP值（秒）)
        """
        try:
            audits = lighthouse_result.get("audits", {})
            lcp_audit = audits.get("largest-contentful-paint", {})
            lcp_ms = lcp_audit.get("numericValue")

            if lcp_ms is None:
                return 0.0, None

            lcp_seconds = lcp_ms / 1000

            if lcp_seconds < 2.5:
                return 5.0, lcp_seconds
            elif lcp_seconds < 4.0:
                return 2.5, lcp_seconds
            else:
                return 0.0, lcp_seconds

        except Exception:
            return 0.0, None

    def _calculate_fid_score(
        self, lighthouse_result: Dict[str, Any]
    ) -> tuple[float, Optional[float]]:
        """
        计算FID得分（使用TBT替代）

        注意: Lighthouse无法直接测量FID（需真实用户交互）
        使用TBT (Total Blocking Time)作为替代指标

        2025标准:
        - TBT <200ms: 5分（等价于FID <100ms）
        - TBT 200-600ms: 2.5分
        - TBT >600ms: 0分

        Returns:
            (得分, TBT值（毫秒）)
        """
        try:
            audits = lighthouse_result.get("audits", {})
            tbt_audit = audits.get("total-blocking-time", {})
            tbt_ms = tbt_audit.get("numericValue")

            if tbt_ms is None:
                return 0.0, None

            if tbt_ms < 200:
                return 5.0, tbt_ms
            elif tbt_ms < 600:
                return 2.5, tbt_ms
            else:
                return 0.0, tbt_ms

        except Exception:
            return 0.0, None

    def _calculate_cls_score(
        self, lighthouse_result: Dict[str, Any]
    ) -> tuple[float, Optional[float]]:
        """
        计算CLS得分

        2025标准:
        - <0.1: 5分（满分）
        - 0.1-0.25: 2.5分（需改进）
        - >0.25: 0分（差）

        Returns:
            (得分, CLS值)
        """
        try:
            audits = lighthouse_result.get("audits", {})
            cls_audit = audits.get("cumulative-layout-shift", {})
            cls_value = cls_audit.get("numericValue")

            if cls_value is None:
                return 0.0, None

            if cls_value < 0.1:
                return 5.0, cls_value
            elif cls_value < 0.25:
                return 2.5, cls_value
            else:
                return 0.0, cls_value

        except Exception:
            return 0.0, None

    def _add_cwv_diagnostics(
        self,
        diagnostics: List[DiagnosticItem],
        lcp_score: float,
        lcp_value: Optional[float],
        fid_score: float,
        fid_value: Optional[float],
        cls_score: float,
        cls_value: Optional[float],
    ):
        """添加CWV诊断项到列表"""

        # LCP诊断
        if lcp_value is not None:
            severity = (
                SeverityLevel.SUCCESS
                if lcp_score >= 5.0
                else (
                    SeverityLevel.WARNING
                    if lcp_score >= 2.5
                    else SeverityLevel.CRITICAL
                )
            )
            diagnostics.append(
                DiagnosticItem(
                    category="core_web_vitals",
                    check_name="lcp",
                    severity=severity,
                    score=lcp_score,
                    message=f"LCP (Largest Contentful Paint): {lcp_value:.2f}s",
                    suggestion=self._get_lcp_suggestion(lcp_value),
                    current_value=f"{lcp_value:.2f}s",
                    expected_value="<2.5s",
                )
            )

        # FID诊断（TBT替代）
        if fid_value is not None:
            severity = (
                SeverityLevel.SUCCESS
                if fid_score >= 5.0
                else (
                    SeverityLevel.WARNING
                    if fid_score >= 2.5
                    else SeverityLevel.CRITICAL
                )
            )
            diagnostics.append(
                DiagnosticItem(
                    category="core_web_vitals",
                    check_name="tbt",
                    severity=severity,
                    score=fid_score,
                    message=f"TBT (Total Blocking Time): {fid_value:.0f}ms",
                    suggestion=self._get_fid_suggestion(fid_value),
                    current_value=f"{fid_value:.0f}ms",
                    expected_value="<200ms",
                )
            )

        # CLS诊断
        if cls_value is not None:
            severity = (
                SeverityLevel.SUCCESS
                if cls_score >= 5.0
                else (
                    SeverityLevel.WARNING
                    if cls_score >= 2.5
                    else SeverityLevel.CRITICAL
                )
            )
            diagnostics.append(
                DiagnosticItem(
                    category="core_web_vitals",
                    check_name="cls",
                    severity=severity,
                    score=cls_score,
                    message=f"CLS (Cumulative Layout Shift): {cls_value:.3f}",
                    suggestion=self._get_cls_suggestion(cls_value),
                    current_value=f"{cls_value:.3f}",
                    expected_value="<0.1",
                )
            )

    def _get_lcp_suggestion(self, lcp_value: float) -> str:
        """根据LCP值生成优化建议"""
        if lcp_value < 2.5:
            return "LCP表现优秀，保持当前优化策略"

        suggestions = [
            "优化图片加载：使用WebP/AVIF格式，添加width/height属性",
            "减少服务器响应时间（TTFB）",
            "使用CDN加速资源加载",
            "移除阻塞渲染的CSS和JavaScript",
        ]
        return "\n".join(f"- {s}" for s in suggestions)

    def _get_fid_suggestion(self, tbt_value: float) -> str:
        """根据TBT值生成优化建议"""
        if tbt_value < 200:
            return "TBT表现优秀，交互性良好"

        suggestions = [
            "拆分长任务（Long Tasks）",
            "优化JavaScript执行时间",
            "使用Web Workers处理后台任务",
            "延迟加载非关键JavaScript",
        ]
        return "\n".join(f"- {s}" for s in suggestions)

    def _get_cls_suggestion(self, cls_value: float) -> str:
        """根据CLS值生成优化建议"""
        if cls_value < 0.1:
            return "CLS表现优秀，视觉稳定性良好"

        suggestions = [
            "为图片和视频添加width/height属性",
            "避免在现有内容上方插入动态内容",
            "使用transform动画替代引起布局变化的属性",
            "预留广告和嵌入内容的空间",
        ]
        return "\n".join(f"- {s}" for s in suggestions)
