from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from md_audit.parsers.markdown_parser import MarkdownParser
from md_audit.engines import (
    RulesEngine,
    AIEngine,
    CoreWebVitalsAnalyzer,
    ContentDepthAnalyzer,
    EEATAnalyzer,
    AISearchOptimizer,
    LinkAnalyzer,
    IntentAnalyzer,
)
from md_audit.models.data_models import SEOReport
from md_audit.config import MarkdownSEOConfig


class MarkdownSEOAnalyzer:
    """Markdown SEO分析协调器（2025 SEO标准）"""

    def __init__(self, config: MarkdownSEOConfig):
        self.config = config
        self.parser = MarkdownParser()
        self.rules_engine = RulesEngine(config)
        self.content_depth_analyzer = ContentDepthAnalyzer(config)
        self.eeat_analyzer = EEATAnalyzer(config)
        self.ai_search_optimizer = AISearchOptimizer(config)
        self.link_analyzer = LinkAnalyzer(config)
        self.intent_analyzer = IntentAnalyzer(config)

        # AI引擎可选（如果配置禁用或API key未设置）
        self.ai_engine = None
        if config.enable_ai_analysis and config.llm_api_key:
            try:
                self.ai_engine = AIEngine(config)
            except ValueError as e:
                print(f"[警告] AI引擎初始化失败：{e}")

        # CWV分析器可选（Lighthouse可能未安装）
        self.cwv_analyzer = None
        try:
            self.cwv_analyzer = CoreWebVitalsAnalyzer()
        except RuntimeError as e:
            print(f"[警告] CWV分析器初始化失败：{e}")

    def analyze(
        self,
        file_path: str,
        user_keywords: list[str] = None,
        cwv_url: Optional[str] = None
    ) -> SEOReport:
        """
        分析Markdown文件（2025 SEO标准）

        Args:
            file_path: Markdown文件路径
            user_keywords: 用户提供的关键词（可选）
            cwv_url: Core Web Vitals评估URL（可选，需Lighthouse）

        Returns:
            完整的SEO诊断报告

        评分体系（2025标准）：
        - 规则引擎: 60分（元数据20 + 结构18 + 相关性12）
        - Schema Markup: 10分
        - Core Web Vitals: 15分（可选，需提供URL）
        - AI内容质量: 15分（可选，需API密钥）
        """
        # Step 1: 解析Markdown
        parsed = self.parser.parse(file_path)

        # Step 2: 确定关键词
        if user_keywords:
            keywords = user_keywords
            extracted = []
        else:
            # 自动提取
            keywords = self.parser.extract_keywords(
                parsed.raw_content,
                max_keywords=self.config.keywords.max_auto_keywords
            )
            extracted = keywords

        diagnostics = []

        # Step 3: 运行基础规则（元数据/结构/关键词）
        meta_score_raw, meta_diags = self.rules_engine.run_metadata(parsed)
        structure_raw, structure_diags = self.rules_engine.run_structure(parsed)
        keyword_raw, keyword_diags = self.rules_engine.run_keyword(parsed, keywords)
        diagnostics.extend(meta_diags + structure_diags + keyword_diags)

        # Step 4: 搜索意图、内容深度、E-E-A-T、AI搜索、链接质量
        intent_res = self.intent_analyzer.analyze(parsed)
        content_depth = self.content_depth_analyzer.analyze(parsed)
        eeat = self.eeat_analyzer.analyze(parsed)
        ai_search = self.ai_search_optimizer.analyze(parsed)
        links = self.link_analyzer.analyze(parsed.links, parsed.word_count)
        diagnostics.extend(
            intent_res["diagnostics"]
            + content_depth["diagnostics"]
            + eeat["diagnostics"]
            + ai_search["diagnostics"]
            + links["diagnostics"]
        )

        # Step 5: CWV（可选，不计入100分）
        cwv_score = 0.0
        if cwv_url and self.cwv_analyzer:
            cwv_score = self.cwv_analyzer.analyze(cwv_url, diagnostics)

        # Step 6: AI 语义（满分10）
        ai_result = None
        ai_score = 0.0
        if self.ai_engine:
            ai_result = self.ai_engine.analyze(parsed, keywords)
            original_ai_score = self.ai_engine.calculate_ai_score(ai_result)  # 0-40
            ai_score = (original_ai_score / 40) * self.config.score_weights.ai_semantic

        # Step 7: 权重归一化到新100分体系（Schema已移除）
        weights = self.config.score_weights
        metadata_score = min(weights.metadata, (meta_score_raw / 25) * weights.metadata)
        structure_core = (structure_raw / 22) * (weights.structure - 3)  # 预留3分给链接
        structure_score = min(weights.structure, structure_core + links["total_link_score"])
        keyword_score = min(weights.keywords, (keyword_raw / 8) * weights.keywords)
        content_depth_score = min(weights.content_depth, content_depth["total_depth_score"])
        eeat_score = min(weights.eeat, eeat["total_eeat_score"])
        ai_search_score = min(weights.ai_search, ai_search["total_geo_score"])
        intent_score = min(weights.intent, intent_res["intent_score"])

        total_score = (
            metadata_score
            + intent_score
            + content_depth_score
            + eeat_score
            + structure_score
            + ai_search_score
            + keyword_score
            + ai_score
        )

        return SEOReport(
            file_path=file_path,
            total_score=round(total_score, 1),
            metadata_score=round(metadata_score, 1),
            intent_score=round(intent_score, 1),
            content_depth_score=round(content_depth_score, 1),
            eeat_score=round(eeat_score, 1),
            structure_score=round(structure_score, 1),
            ai_search_score=round(ai_search_score, 1),
            keyword_score=round(keyword_score, 1),
            schema_score=0.0,  # Schema已移除，保持字段兼容
            ai_score=round(ai_score, 1),
            relevance_score=round(keyword_score, 1),
            cwv_score=round(cwv_score, 1),
            diagnostics=diagnostics,
            ai_analysis=ai_result,
            extracted_keywords=extracted,
            user_keywords=user_keywords or [],
            cwv_url=cwv_url
        )

    def analyze_directory(
        self,
        directory: str,
        user_keywords: Optional[List[str]] = None,
        max_workers: int = 4,
        show_progress: bool = True
    ) -> List[SEOReport]:
        """
        批量分析目录中的所有Markdown文件

        Args:
            directory: 目录路径
            user_keywords: 用户提供的关键词（应用于所有文件）
            max_workers: 并发工作线程数
            show_progress: 是否显示进度条（文件数>10时）

        Returns:
            所有文件的SEO报告列表
        """
        # 递归查找所有.md文件
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"目录不存在: {directory}")
        if not dir_path.is_dir():
            raise NotADirectoryError(f"路径不是目录: {directory}")

        md_files = list(dir_path.rglob("*.md"))
        if not md_files:
            print(f"警告：目录 {directory} 中未找到.md文件")
            return []

        print(f"找到 {len(md_files)} 个Markdown文件")

        # 判断是否需要进度条
        use_progress = show_progress and len(md_files) > 10

        # 并发处理
        reports = []
        failed_files = []

        if use_progress:
            try:
                from rich.progress import Progress, TaskID
                with Progress() as progress:
                    task = progress.add_task("[cyan]分析中...", total=len(md_files))

                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        future_to_file = {
                            executor.submit(self._analyze_safe, str(file), user_keywords): file
                            for file in md_files
                        }

                        for future in as_completed(future_to_file):
                            file = future_to_file[future]
                            try:
                                report = future.result()
                                if report:
                                    reports.append(report)
                                else:
                                    failed_files.append(str(file))
                            except Exception as e:
                                print(f"[错误] 处理文件 {file} 失败: {e}")
                                failed_files.append(str(file))
                            finally:
                                progress.update(task, advance=1)
            except ImportError:
                # rich未安装，回退到无进度条模式
                print("[警告] rich库未安装，无法显示进度条（pip install rich）")
                use_progress = False

        if not use_progress:
            # 无进度条模式
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(self._analyze_safe, str(file), user_keywords): file
                    for file in md_files
                }

                for future in as_completed(future_to_file):
                    file = future_to_file[future]
                    try:
                        report = future.result()
                        if report:
                            reports.append(report)
                        else:
                            failed_files.append(str(file))
                    except Exception as e:
                        print(f"[错误] 处理文件 {file} 失败: {e}")
                        failed_files.append(str(file))

        # 输出统计
        print(f"\n✅ 成功分析: {len(reports)} 个文件")
        if failed_files:
            print(f"❌ 失败: {len(failed_files)} 个文件")
            for f in failed_files[:5]:  # 只显示前5个
                print(f"  - {f}")
            if len(failed_files) > 5:
                print(f"  ... 还有 {len(failed_files) - 5} 个")

        return reports

    def _analyze_safe(
        self,
        file_path: str,
        user_keywords: Optional[List[str]] = None
    ) -> Optional[SEOReport]:
        """
        安全分析单个文件（捕获异常，返回None而非抛出）

        Args:
            file_path: 文件路径
            user_keywords: 用户关键词

        Returns:
            SEO报告或None（失败时）
        """
        try:
            return self.analyze(file_path, user_keywords)
        except FileNotFoundError:
            print(f"[跳过] 文件不存在: {file_path}")
            return None
        except UnicodeDecodeError:
            print(f"[跳过] 文件编码错误: {file_path}")
            return None
        except PermissionError:
            print(f"[跳过] 无读取权限: {file_path}")
            return None
        except Exception as e:
            print(f"[跳过] 分析失败 {file_path}: {type(e).__name__}: {e}")
            return None
