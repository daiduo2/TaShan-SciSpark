"""
    paper模块路由入口
"""
from fastapi import APIRouter

from app.api.paper import paper_api

paper_module_router = APIRouter(prefix="/paper")

paper_module_router.include_router(paper_api.router, tags=["论文助手模块"])