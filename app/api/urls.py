from fastapi import APIRouter, Depends


from app.api.paper.urls import paper_module_router
router = APIRouter()
router.include_router(paper_module_router)
