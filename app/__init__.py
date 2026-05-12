import os
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

# 数据目录
DATA_DIR = ROOT_DIR / "data"
EXPORT_DIR = ROOT_DIR / "exports"

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

# 版本信息
__version__ = "1.0.0"
__author__ = "罗喆帆"
__description__ = "基于用户故事的测试用例辅助生成系统"

__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__description__",
    
    # 路径常量
    "ROOT_DIR",
    "DATA_DIR",
    "EXPORT_DIR",
]

# 初始化日志（可选）
def setup_logging():
    """配置日志系统"""
    import logging
    from dotenv import load_dotenv
    
    # 加载环境变量
    load_dotenv(ROOT_DIR / ".env")
    
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", None)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            *( [logging.FileHandler(ROOT_DIR / log_file)] if log_file else [] )
        ]
    )
    
    return logging.getLogger(__name__)

# 可选：自动配置日志
# logger = setup_logging()