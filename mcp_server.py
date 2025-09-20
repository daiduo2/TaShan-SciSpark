#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AstroInsight MCP Server
学术论文研究助手的MCP服务器实现
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 抑制第三方库的警告
from suppress_warnings import apply_warning_filters
apply_warning_filters()

try:
    from fastmcp import FastMCP
except ImportError:
    print("请安装fastmcp: pip install fastmcp")
    sys.exit(1)

# 导入项目模块
from main import main as astro_main
from app.utils.tool import (
    get_related_keyword, 
    extract_technical_entities, 
    extract_message,
    review_mechanism,
    paper_compression
)
from app.utils.arxiv_api import search_paper
from app.utils.llm_api import call_with_deepseek, call_with_qwenmax
from app.core.config import OUTPUT_PATH
from app.task.paper_assistant import paper_assistant

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server.log'),
        logging.StreamHandler(sys.stderr)  # 使用stderr避免与stdio传输冲突
    ]
)
logger = logging.getLogger(__name__)

# 创建FastMCP实例
mcp = FastMCP("AstroInsight")

class TaskManager:
    """任务管理器，用于管理异步任务"""
    
    def __init__(self):
        self.tasks = {}
    
    def create_task(self, task_type: str, params: Dict[str, Any]) -> str:
        """创建新任务"""
        task_id = f"task_{len(self.tasks) + 1}_{int(datetime.now().timestamp())}"
        self.tasks[task_id] = {
            "id": task_id,
            "type": task_type,
            "status": "pending",
            "params": params,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "result": None,
            "error": None,
            "progress": 0
        }
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, status: str, result: Any = None, error: str = None):
        """更新任务状态"""
        if task_id in self.tasks:
            self.tasks[task_id].update({
                "status": status,
                "updated_at": datetime.now().isoformat(),
                "result": result,
                "error": error,
                "progress": 100 if status == "completed" else 50 if status == "running" else 0
            })

# 全局任务管理器
task_manager = TaskManager()

@mcp.tool
def search_papers(keyword: str, limit: int = 5) -> Dict[str, Any]:
    """
    搜索学术论文
    
    Args:
        keyword: 搜索关键词
        limit: 返回论文数量限制，默认5篇
    
    Returns:
        包含论文列表的字典
    """
    try:
        logger.info(f"搜索论文，关键词: {keyword}, 限制: {limit}")
        
        # 调用arxiv搜索
        papers = search_paper(keyword, limit)
        
        if not papers:
            return {
                "success": False,
                "message": "未找到相关论文",
                "papers": []
            }
        
        # 格式化论文信息
        formatted_papers = []
        for paper in papers:
            formatted_paper = {
                "title": paper.get("title", ""),
                "authors": paper.get("authors", []),
                "abstract": paper.get("abstract", ""),
                "published": paper.get("published", ""),
                "url": paper.get("url", ""),
                "pdf_url": paper.get("pdf_url", "")
            }
            formatted_papers.append(formatted_paper)
        
        logger.info(f"成功搜索到 {len(formatted_papers)} 篇论文")
        return {
            "success": True,
            "message": f"成功搜索到 {len(formatted_papers)} 篇论文",
            "papers": formatted_papers
        }
        
    except Exception as e:
        logger.error(f"搜索论文时出错: {str(e)}")
        return {
            "success": False,
            "message": f"搜索论文时出错: {str(e)}",
            "papers": []
        }

@mcp.tool
def extract_keywords(text: str, split_section: str = "Paper Abstract") -> Dict[str, Any]:
    """
    从文本中提取技术关键词
    
    Args:
        text: 要分析的文本内容
        split_section: 文本分割部分，默认为"Paper Abstract"
    
    Returns:
        包含提取的关键词列表的字典
    """
    try:
        logger.info(f"提取关键词，文本长度: {len(text)}")
        
        # 调用关键词提取函数
        keywords = extract_technical_entities(text, split_section)
        
        if not keywords:
            return {
                "success": False,
                "message": "未能提取到关键词",
                "keywords": []
            }
        
        logger.info(f"成功提取到 {len(keywords)} 个关键词")
        return {
            "success": True,
            "message": f"成功提取到 {len(keywords)} 个关键词",
            "keywords": keywords
        }
        
    except Exception as e:
        logger.error(f"提取关键词时出错: {str(e)}")
        return {
            "success": False,
            "message": f"提取关键词时出错: {str(e)}",
            "keywords": []
        }

@mcp.tool
def generate_research_idea(keyword: str, paper_count: int = 3) -> Dict[str, Any]:
    """
    生成研究想法（异步任务）
    
    Args:
        keyword: 研究关键词
        paper_count: 参考论文数量，默认3篇
    
    Returns:
        包含任务ID的字典，可用于查询任务状态
    """
    try:
        logger.info(f"创建研究想法生成任务，关键词: {keyword}, 论文数量: {paper_count}")
        
        # 创建异步任务
        task_id = task_manager.create_task("generate_research_idea", {
            "keyword": keyword,
            "paper_count": paper_count
        })
        
        # 启动异步任务
        asyncio.create_task(_generate_research_idea_async(task_id, keyword, paper_count))
        
        return {
            "success": True,
            "message": "研究想法生成任务已启动",
            "task_id": task_id
        }
        
    except Exception as e:
        logger.error(f"创建研究想法生成任务时出错: {str(e)}")
        return {
            "success": False,
            "message": f"创建任务时出错: {str(e)}",
            "task_id": None
        }

async def _generate_research_idea_async(task_id: str, keyword: str, paper_count: int):
    """异步生成研究想法"""
    try:
        task_manager.update_task(task_id, "running")
        logger.info(f"开始执行研究想法生成任务: {task_id}")
        
        # 调用主程序生成研究想法
        result = await asyncio.get_event_loop().run_in_executor(
            None, astro_main, keyword, paper_count
        )
        
        task_manager.update_task(task_id, "completed", result)
        logger.info(f"研究想法生成任务完成: {task_id}")
        
    except Exception as e:
        error_msg = f"生成研究想法时出错: {str(e)}"
        task_manager.update_task(task_id, "failed", error=error_msg)
        logger.error(f"任务 {task_id} 失败: {error_msg}")

@mcp.tool
def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
    
    Returns:
        包含任务状态信息的字典
    """
    try:
        task = task_manager.get_task(task_id)
        
        if not task:
            return {
                "success": False,
                "message": f"未找到任务: {task_id}",
                "task": None
            }
        
        return {
            "success": True,
            "message": "任务状态获取成功",
            "task": {
                "id": task["id"],
                "type": task["type"],
                "status": task["status"],
                "progress": task["progress"],
                "created_at": task["created_at"],
                "updated_at": task["updated_at"],
                "error": task["error"]
            }
        }
        
    except Exception as e:
        logger.error(f"获取任务状态时出错: {str(e)}")
        return {
            "success": False,
            "message": f"获取任务状态时出错: {str(e)}",
            "task": None
        }

@mcp.tool
def review_research_idea(topic: str, draft: str) -> Dict[str, Any]:
    """
    评审研究想法
    
    Args:
        topic: 研究主题
        draft: 研究想法草稿
    
    Returns:
        包含评审结果的字典
    """
    try:
        logger.info(f"评审研究想法，主题: {topic}")
        
        # 调用评审机制
        review_result = review_mechanism(topic, draft)
        
        if not review_result:
            return {
                "success": False,
                "message": "评审失败",
                "review": None
            }
        
        return {
            "success": True,
            "message": "评审完成",
            "review": review_result
        }
        
    except Exception as e:
        logger.error(f"评审研究想法时出错: {str(e)}")
        return {
            "success": False,
            "message": f"评审时出错: {str(e)}",
            "review": None
        }

@mcp.tool
def compress_paper_content(title: str, abstract: str, content: str = "") -> Dict[str, Any]:
    """
    压缩论文内容
    
    Args:
        title: 论文标题
        abstract: 论文摘要
        content: 论文正文内容（可选）
    
    Returns:
        包含压缩结果的字典
    """
    try:
        logger.info(f"压缩论文内容，标题: {title[:50]}...")
        
        # 调用论文压缩函数
        compressed_result = paper_compression(title, abstract, content)
        
        if not compressed_result:
            return {
                "success": False,
                "message": "压缩失败",
                "compressed_content": None
            }
        
        return {
            "success": True,
            "message": "压缩完成",
            "compressed_content": compressed_result
        }
        
    except Exception as e:
        logger.error(f"压缩论文内容时出错: {str(e)}")
        return {
            "success": False,
            "message": f"压缩时出错: {str(e)}",
            "compressed_content": None
        }

@mcp.tool
def get_server_info() -> Dict[str, Any]:
    """
    获取服务器信息
    
    Returns:
        包含服务器信息的字典
    """
    return {
        "name": "AstroInsight MCP Server",
        "version": "1.0.0",
        "description": "学术论文研究助手的MCP服务器",
        "tools": [
            "search_papers",
            "extract_keywords", 
            "generate_research_idea",
            "get_task_status",
            "review_research_idea",
            "compress_paper_content",
            "get_server_info"
        ],
        "status": "running"
    }

if __name__ == "__main__":
    logger.info("启动AstroInsight MCP服务器")
    # 运行MCP服务器
    mcp.run(transport="stdio")