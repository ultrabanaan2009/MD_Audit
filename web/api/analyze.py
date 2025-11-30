# 分析API路由
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List

from web.services.file_service import FileService
from web.services.analyzer_service import AnalyzerService
from web.services.history_service import HistoryService
from web.models.responses import AnalyzeResponse, ErrorResponse, BatchAnalyzeResponse, BatchAnalyzeItem


router = APIRouter(prefix="/api/v1", tags=["analyze"])
limiter = Limiter(key_func=get_remote_address)


# 依赖注入（单例服务）
def get_file_service():
    return FileService()


def get_analyzer_service():
    return AnalyzerService()


def get_history_service():
    return HistoryService()


@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("10/minute")  # 上传限流（放宽到10次/分钟，便于开发测试）
async def analyze_file(
    request: Request,  # slowapi需要request参数
    file: UploadFile = File(..., description="Markdown文件"),
    file_service: FileService = Depends(get_file_service),
    analyzer_service: AnalyzerService = Depends(get_analyzer_service),
    history_service: HistoryService = Depends(get_history_service),
):
    """
    单文件诊断API

    - **file**: 上传的Markdown文件（<10MB，.md/.txt/.markdown）
    - **keywords**: 用户关键词（可选，Query参数或JSON body）
    """
    try:
        # 1. 保存上传文件
        temp_file = await file_service.save_upload(file)

        # 2. 执行分析（复用现有analyzer）
        report = analyzer_service.analyze_file(str(temp_file))

        # 3. 保存历史记录
        report_dict = report.model_dump()  # Pydantic序列化
        history_id = history_service.save_report(report_dict, file.filename)

        # 4. 清理临时文件
        temp_file.unlink()

        return AnalyzeResponse(report=report_dict, history_id=history_id)

    except ValueError as e:
        # 文件校验错误
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error_code="INVALID_INPUT",
                message=str(e),
                suggestion="请检查文件格式和大小"
            ).model_dump()
        )

    except Exception as e:
        # 分析失败
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code="ANALYSIS_FAILED",
                message="诊断失败，请稍后重试",
                suggestion="如果问题持续，请联系管理员",
                details=str(e)
            ).model_dump()
        )


@router.post("/analyze/batch", response_model=BatchAnalyzeResponse)
@limiter.limit("5/minute")  # 批量分析限流更严格
async def analyze_batch(
    request: Request,
    files: List[UploadFile] = File(..., description="多个Markdown文件"),
    file_service: FileService = Depends(get_file_service),
    analyzer_service: AnalyzerService = Depends(get_analyzer_service),
    history_service: HistoryService = Depends(get_history_service),
):
    """
    批量文件诊断API

    - **files**: 多个上传的Markdown文件（每个<10MB，.md/.txt/.markdown）
    - 最多支持50个文件同时上传
    """
    if len(files) > 50:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error_code="TOO_MANY_FILES",
                message="文件数量超过限制",
                suggestion="每次最多上传50个文件"
            ).model_dump()
        )

    results = []
    success_count = 0
    failed_count = 0
    total_score = 0.0

    for file in files:
        try:
            # 1. 保存上传文件
            temp_file = await file_service.save_upload(file)

            # 2. 执行分析
            report = analyzer_service.analyze_file(str(temp_file))
            report_dict = report.model_dump()

            # 3. 保存历史记录
            history_id = history_service.save_report(report_dict, file.filename)

            # 4. 清理临时文件
            temp_file.unlink()

            # 5. 记录结果
            results.append(BatchAnalyzeItem(
                file_name=file.filename,
                total_score=report.total_score,
                rules_score=report.rules_score,
                ai_score=report.ai_score,
                history_id=history_id,
                success=True
            ))
            success_count += 1
            total_score += report.total_score

        except Exception as e:
            results.append(BatchAnalyzeItem(
                file_name=file.filename,
                total_score=0,
                rules_score=0,
                ai_score=0,
                history_id="",
                success=False,
                error=str(e)
            ))
            failed_count += 1

    # 计算平均分
    average_score = total_score / success_count if success_count > 0 else 0

    return BatchAnalyzeResponse(
        total_files=len(files),
        success_count=success_count,
        failed_count=failed_count,
        results=results,
        average_score=round(average_score, 1)
    )
