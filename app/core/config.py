#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2025/8/23 10:33
# @Author : 桐
# @QQ:1041264242
# 注意事项：
from openai import OpenAI
from py2neo import Graph
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    # 本项目配置
    MINERU_API_TOKEN: str = ""
    QWEN_API_TOKEN: str = ""
    DEEPSEEK_API_TOKEN: str = ""
    DEEPSEEK_API_BASE_URL: str = "https://api.deepseek.com/v1"
    NEO4J_USERNAME: str = ""
    NEO4J_PASSWORD: str = ""
    NEO4J_HOST: str = ""
    NEO4J_PORT: str = ""
    PAPER_ASSISTANT_OUTPUT_PATH: str = "./temp"
    
    # 代理配置（可选）
    HTTP_PROXY: str = ""
    HTTPS_PROXY: str = ""

    # Redis配置
    REDIS_SERVER: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB_INDEX: int = 0

settings = Settings()

OUTPUT_PATH=settings.PAPER_ASSISTANT_OUTPUT_PATH #这里为结果文件输出路径

#MinerU Token配置
MinerU_Token=settings.MINERU_API_TOKEN

# 代理地址配置
# 从环境变量读取代理配置，如果未设置则不使用代理
def get_proxies():
    """
    获取代理配置
    Returns:
        dict: 代理配置字典，如果未配置代理则返回空字典
    """
    proxies = {}
    if settings.HTTP_PROXY:
        proxies['http'] = settings.HTTP_PROXY
    if settings.HTTPS_PROXY:
        proxies['https'] = settings.HTTPS_PROXY
    return proxies

Proxies = get_proxies()

#大模型API配置
DeepSeek_Key=OpenAI(api_key=settings.DEEPSEEK_API_TOKEN, base_url=settings.DEEPSEEK_API_BASE_URL)
QwenMax_Key=settings.QWEN_API_TOKEN

#neo4j 实体库接口配置
neo4j_url = f"bolt://{settings.NEO4J_HOST}:{settings.NEO4J_PORT}"
neo4j_username = settings.NEO4J_USERNAME
neo4j_password = settings.NEO4J_PASSWORD

# 使用正确的py2neo API创建Graph连接
try:
    graph = Graph(neo4j_url, auth=(neo4j_username, neo4j_password))
    # 测试连接是否可用
    graph.run("RETURN 1").data()
    print("Neo4j连接成功")
except Exception as e:
    print(f"Neo4j连接失败: {e}")
    graph = None