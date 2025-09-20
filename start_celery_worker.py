#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Celery Worker启动脚本
优化内存管理和性能配置
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_optimal_worker_config():
    """
    根据系统资源获取最优的Worker配置
    
    Returns:
        dict: Worker配置参数
    """
    import psutil
    
    # 获取系统内存信息
    memory_gb = psutil.virtual_memory().total / (1024**3)
    cpu_count = psutil.cpu_count()
    
    logger.info(f"系统配置: 内存={memory_gb:.1f}GB, CPU核心数={cpu_count}")
    
    # Windows系统使用solo池解决兼容性问题
    import platform
    if platform.system() == "Windows":
        # Windows系统强制使用solo池，避免prefork和gevent兼容性问题
        pool_type = "solo"
        concurrency = 1  # solo池只支持单进程
        max_memory_per_child = 512 * 1024  # 512MB
        max_tasks_per_child = 100
        logger.info("检测到Windows系统，使用solo池避免兼容性问题")
    else:
        # Linux/Unix系统使用传统配置
        if memory_gb >= 16:
            # 高内存系统
            pool_type = "prefork"
            concurrency = min(cpu_count, 4)
            max_memory_per_child = 512 * 1024  # 512MB
            max_tasks_per_child = 50
        elif memory_gb >= 8:
            # 中等内存系统
            pool_type = "prefork"
            concurrency = min(cpu_count, 2)
            max_memory_per_child = 256 * 1024  # 256MB
            max_tasks_per_child = 20
        else:
            # 低内存系统
            pool_type = "solo"
            concurrency = 1
            max_memory_per_child = 128 * 1024  # 128MB
            max_tasks_per_child = 10
    
    config = {
        'pool': pool_type,
        'concurrency': concurrency,
        'max_memory_per_child': max_memory_per_child,
        'max_tasks_per_child': max_tasks_per_child
    }
    
    logger.info(f"选择的Worker配置: {config}")
    return config

def clear_celery_queues():
    """
    清空Celery任务队列和结果存储
    """
    try:
        logger.info("正在清空Celery任务队列...")
        
        # 导入Celery应用
        from app.core.celery import celery_app
        
        # 清空所有队列
        celery_app.control.purge()
        logger.info("✓ 已清空任务队列")
        
        # 清空结果后端
        try:
            import redis
            from app.core.config import settings
            
            # 连接到结果存储的Redis数据库
            result_redis_db_index = 6
            r = redis.Redis(
                host=settings.REDIS_SERVER,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=result_redis_db_index,
                decode_responses=True
            )
            
            # 清空结果数据库
            r.flushdb()
            logger.info("✓ 已清空结果存储")
            
            # 同时清空消息队列数据库
            broker_redis_db_index = 5
            r_broker = redis.Redis(
                host=settings.REDIS_SERVER,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=broker_redis_db_index,
                decode_responses=True
            )
            r_broker.flushdb()
            logger.info("✓ 已清空消息队列存储")
            
        except Exception as e:
            logger.warning(f"清空Redis存储时出现警告: {e}")
        
        logger.info("队列清空完成，Worker将以干净状态启动")
        
    except Exception as e:
        logger.error(f"清空队列失败: {e}")
        # 不阻止启动，只是记录错误
        logger.info("将继续启动Worker...")

def clear_celery_queues():
    """
    清空Celery任务队列和结果后端
    """
    try:
        logger.info("正在清空Celery任务队列和结果后端...")
        
        # 导入Celery应用
        from app.core.celery import celery_app
        
        # 清空所有队列
        celery_app.control.purge()
        logger.info("✓ 已清空任务队列")
        
        # 清空结果后端
        try:
            import redis
            from app.core.config import settings
            
            # 连接到结果后端Redis数据库
            result_redis_db_index = 6
            redis_client = redis.Redis(
                host=settings.REDIS_SERVER,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=result_redis_db_index,
                decode_responses=True
            )
            
            # 清空结果后端数据库
            redis_client.flushdb()
            logger.info("✓ 已清空结果后端")
            
            # 同时清空消息队列数据库
            broker_redis_db_index = 5
            broker_redis_client = redis.Redis(
                host=settings.REDIS_SERVER,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=broker_redis_db_index,
                decode_responses=True
            )
            broker_redis_client.flushdb()
            logger.info("✓ 已清空消息队列")
            
        except Exception as e:
            logger.warning(f"清空Redis数据库时出现警告: {e}")
        
        logger.info("队列清空完成，Worker将以干净状态启动")
        
    except Exception as e:
        logger.error(f"清空队列失败: {e}")
        # 不阻止启动，只是记录错误
        logger.info("继续启动Worker...")

def start_celery_worker():
    """
    启动Celery Worker进程
    """
    try:
        # 获取项目根目录
        project_root = Path(__file__).parent
        os.chdir(project_root)
        
        # 添加项目路径到Python路径
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # 清空任务队列和结果后端
        clear_celery_queues()
        
        # 获取最优配置
        config = get_optimal_worker_config()
        
        # 构建Celery启动命令 - 使用简化配置避免参数冲突
        cmd = [
            sys.executable, "-m", "celery",
            "-A", "app.core.celery:celery_app",  # 明确指定celery_app变量
            "worker",
            f"--pool={config['pool']}",
            f"--concurrency={config['concurrency']}",
            "--loglevel=info"
        ]
        
        # 设置环境变量 - 简化配置
        env = os.environ.copy()
        env.update({
            'PYTHONPATH': str(project_root),
            'PYTHONUNBUFFERED': '1'
        })
        
        logger.info(f"启动Celery Worker命令: {' '.join(cmd)}")
        logger.info("正在启动Celery Worker...")
        
        # 启动Worker进程
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 实时输出日志
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(line.rstrip())
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭Worker...")
            process.terminate()
            process.wait()
            logger.info("Worker已关闭")
        
    except Exception as e:
        logger.error(f"启动Celery Worker失败: {e}")
        raise

def check_dependencies():
    """
    检查必要的依赖包和模块是否可用
    """
    try:
        print("检查依赖包...")
        import celery
        import redis
        import psutil
        print(f"✓ Celery版本: {celery.__version__}")
        print(f"✓ Redis包可用")
        print(f"✓ Psutil包可用")
        
        # 检查任务模块是否可以导入
        print("检查任务模块...")
        from app.core.celery import celery_app
        print("✓ Celery应用导入成功")
        
        # 检查任务是否注册
        registered_tasks = list(celery_app.tasks.keys())
        print(f"✓ 已注册任务: {registered_tasks}")
        
        return True
    except ImportError as e:
        print(f"✗ 依赖检查失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 模块检查失败: {e}")
        return False

def main():
    """
    主函数：启动优化的Celery Worker
    """
    print("=== Celery Worker 启动器 ===")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    
    # 检查依赖
    if not check_dependencies():
        print("依赖检查失败，无法启动Worker")
        sys.exit(1)
    
    try:
        start_celery_worker()
    except KeyboardInterrupt:
        logger.info("用户中断，退出程序")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()