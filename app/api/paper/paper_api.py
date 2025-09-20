from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from starlette import status

from app.api.common import BaseAPI
from app.core.celery import celery_app
from main import main
from app.task.paper_assistant import paper_assistant

router = APIRouter()


class RAGAPI(BaseAPI):
    """
    RAG API类，提供文档处理和查询接口
    """

    @staticmethod
    @router.post("/generate_paper",
                 summary="生成论文",
                 description="生成论文"
                 )
    async def generate_paper(Keyword: str):
        """
        生成论文

        Args:
            Keyword : 关键词

        Returns:
            创建结果响应
        """
        try:
            task = paper_assistant.delay(Keyword=Keyword, SearchPaperNum=2)
            return BaseAPI.success(data={"task_id": task.id})
        except ValueError as e:
            return BaseAPI.error(code=status.HTTP_400_BAD_REQUEST,
                                 message=str(e),
                                 status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return BaseAPI.error(code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                 message=f"内部服务器错误: {str(e)}",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    @router.post("/get_status",
                 summary="获取结果",
                 description="获取结果"
                 )
    async def generate_paper(task_id: str):
        """
        获取结果

        Args:
            task_id : 任务id

        Returns:
            创建结果响应
        """
        try:
            task_result = AsyncResult(task_id, app=celery_app)
            return BaseAPI.success(data={"task_result": task_result.result})
        except ValueError as e:
            return BaseAPI.error(code=status.HTTP_400_BAD_REQUEST,
                                 message=str(e),
                                 status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return BaseAPI.error(code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                 message=f"内部服务器错误: {str(e)}",
                                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)