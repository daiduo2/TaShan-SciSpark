from celery import Celery

from app.core.config import settings

# 使用Redis作为消息代理和结果后端
redis_db_index = 5
broker_store = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_SERVER}:{settings.REDIS_PORT}/{redis_db_index}"

# 使用不同的Redis数据库索引存储结果，避免与消息队列冲突
result_redis_db_index = 6
result_backend_store = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_SERVER}:{settings.REDIS_PORT}/{result_redis_db_index}"

celery_app = Celery('tasks', broker=broker_store, result_backend=result_backend_store)

# 配置Celery
celery_app.conf.update(
    # 基础配置
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # 使用autodiscover_tasks自动发现任务，同时显式包含任务模块作为备选
    include=['app.task.paper_assistant'],  # 显式包含任务模块，确保任务被注册
    
    # 内存管理配置
    worker_max_memory_per_child=1024 * 1024,  # 1GB内存限制，超过后重启worker进程
    worker_max_tasks_per_child=1,  # 每个worker进程只处理1个任务后重启，防止内存累积
    
    # 任务时间限制
    task_soft_time_limit=1800,  # 30分钟软限制
    task_time_limit=2400,  # 40分钟硬限制
    
    # Worker配置
    worker_prefetch_multiplier=1,  # 每个worker只预取1个任务，避免内存预占用
    worker_disable_rate_limits=True,  # 禁用速率限制以提高性能
    
    # 任务结果配置
    result_expires=3600,  # 结果1小时后过期，及时清理
    task_ignore_result=False,  # 保留结果以便查询状态
    
    # 序列化优化
    task_compression='gzip',  # 启用任务压缩，减少内存占用
    result_compression='gzip',  # 启用结果压缩
    
    # 错误处理和后端配置
    task_reject_on_worker_lost=True,  # worker丢失时拒绝任务
    task_acks_late=True,  # 任务完成后才确认，确保可靠性
    
    # 异常序列化配置 - 解决"Exception information must include the exception type"问题
    task_send_sent_event=True,  # 发送任务发送事件
    task_track_started=True,  # 跟踪任务开始状态
    worker_send_task_events=True,  # 发送任务事件
    
    # 结果后端配置优化
    result_backend_transport_options={
        'retry_on_timeout': True,
        'visibility_timeout': 3600,
        'fanout_prefix': True,
        'fanout_patterns': True,
        # 添加异常处理相关配置
        'master_name': None,
        'socket_keepalive': True,
        'socket_keepalive_options': {},
        'health_check_interval': 30,
    },
    
    # 强制清理旧的异常数据，避免序列化问题
    result_persistent=False,  # 不持久化结果，避免旧数据干扰
    task_store_errors_even_if_ignored=True,  # 即使忽略结果也存储错误信息
    
    # 异常传播配置
    task_always_eager=False,  # 确保任务异步执行
    task_eager_propagates=True,  # 在eager模式下传播异常
    
    # 添加异常序列化配置，确保异常可以正确序列化
    task_serializer_options={
        'ensure_ascii': False,
        'separators': (',', ':')
    },
    result_serializer_options={
        'ensure_ascii': False,
        'separators': (',', ':')
    }
)

# 自动发现任务模块
celery_app.autodiscover_tasks(['app.task'])