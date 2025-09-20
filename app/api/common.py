import json
from typing import ClassVar

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette import status
from starlette.responses import JSONResponse, StreamingResponse


class ErrorAPIResponse(BaseModel):
    """
        API错误响应内容
    """
    code: int
    message: str
    data: dict = {}


class SuccessAPIResponse(BaseModel):
    """
        API成功响应内容
    """
    code: int = 200
    message: str = 'success'
    data: dict = {}


class StreamAPIResponse(BaseModel):
    """
        stream流式响应内容
    """

    HEADERS: ClassVar[dict] = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    }
    MEDIA_TYPE: ClassVar[str] = "text/event-stream"

    @staticmethod
    async def error_stream_gen():
        """
            错误stream流返回信息
        """
        error_message = {
            "choices": [{"delta": {"role": "assistant", "content": "当前操作无法完成，请稍后再试"}}]}
        chunks = [
            f"data: {json.dumps(error_message, ensure_ascii=False)}\n\n",  # 错误消息
            "data: [DONE]\n\n"
        ]
        for chunk in chunks:
            yield chunk


class BaseAPI(object):
    """
        基础API类
    """

    @staticmethod
    def success(data: any, message: str = "success", code: int = 200, status_code: int = status.HTTP_200_OK):
        response_data = SuccessAPIResponse(code=code, message=message, data=data)
        return JSONResponse(content=jsonable_encoder(response_data), status_code=status_code)

    @staticmethod
    def error(code: int, message: str, status_code: int, data: dict = None):
        if data is None:
            data = {}
        response_data = ErrorAPIResponse(code=code, message=message, data=data)
        return JSONResponse(content=jsonable_encoder(response_data), status_code=status_code)

    @staticmethod
    def success_stream_response(stream_gen, **kwargs):
        return StreamingResponse(stream_gen, media_type=StreamAPIResponse.MEDIA_TYPE,
                                 headers=StreamAPIResponse.HEADERS, **kwargs)

    @staticmethod
    def error_stream_response(**kwargs):
        return StreamingResponse(StreamAPIResponse.error_stream_gen(), media_type=StreamAPIResponse.MEDIA_TYPE,
                                 headers=StreamAPIResponse.HEADERS, **kwargs)