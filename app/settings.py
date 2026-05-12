import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv, set_key, unset_key

router = APIRouter(prefix="/settings", tags=["系统设置"])

# 确定 .env 文件路径
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

class SettingsModel(BaseModel):
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    llm_provider: str = "qwen"
    llm_model: str = "qwen-max"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 4096
    enable_llm: bool = True
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    dashscope_api_key: str = ""

@router.get("")
async def get_settings():
    """获取当前 .env 配置（只返回非敏感字段或全部，这里为方便一律返回）"""
    # 重新加载确保最新（如果外部修改了 .env）
    load_dotenv(ENV_PATH, override=True)
    settings = {
        "api_host": os.getenv("API_HOST", "0.0.0.0"),
        "api_port": int(os.getenv("API_PORT", "8000")),
        "llm_provider": os.getenv("LLM_PROVIDER", "qwen"),
        "llm_model": os.getenv("LLM_MODEL", "qwen-max"),
        "llm_temperature": float(os.getenv("LLM_TEMPERATURE", "0.3")),
        "llm_max_tokens": int(os.getenv("LLM_MAX_TOKENS", "4096")),
        "enable_llm": os.getenv("ENABLE_LLM_ENHANCEMENT", "true").lower() == "true",
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "dashscope_api_key": os.getenv("DASHCOPE_API_KEY", "")
    }
    return settings

@router.post("")
async def update_settings(settings: SettingsModel):
    """更新 .env 文件并重新加载环境变量"""
    try:
        # 写入各个配置项
        env_map = {
            "API_HOST": settings.api_host,
            "API_PORT": str(settings.api_port),
            "LLM_PROVIDER": settings.llm_provider,
            "LLM_MODEL": settings.llm_model,
            "LLM_TEMPERATURE": str(settings.llm_temperature),
            "LLM_MAX_TOKENS": str(settings.llm_max_tokens),
            "ENABLE_LLM_ENHANCEMENT": "true" if settings.enable_llm else "false",
            "OPENAI_API_KEY": settings.openai_api_key,
            "DEEPSEEK_API_KEY": settings.deepseek_api_key,
            "DASHCOPE_API_KEY": settings.dashscope_api_key
        }
        
        for key, value in env_map.items():
            set_key(ENV_PATH, key, value)
        
        # 重新加载环境变量
        load_dotenv(ENV_PATH, override=True)
        return {"success": True, "message": "配置已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入 .env 文件失败: {str(e)}")