import hashlib
import logging
from typing import Any
from django_redis import get_redis_connection

logger = logging.getLogger(__name__)

# 建议：尽量不要在模块顶层直接建立连接，但在现有架构下保持不变以兼容旧代码
# 如果可能，建议在具体使用 Redis 的函数内部调用 get_redis_connection("default")
redis_client = get_redis_connection("default")

def generate_cache_key(prefix: str, value: Any) -> str:
    """
    生成缓存键。
    优化点：增加了对非字符串类型的兼容，防止 AttributeError。
    """
    if value is None:
        value = ""
    
    # 1. 强转字符串：防止传入 int/dict 等类型导致 .encode() 报错
    # 2. 指定编码：虽然默认是 utf-8，显式指定更安全
    value_str = str(value)
    
    # 3. 计算 MD5
    value_hash = hashlib.md5(value_str.encode('utf-8')).hexdigest()
    
    return f"{prefix}:{value_hash}"