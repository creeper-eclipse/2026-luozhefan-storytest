from dotenv import load_dotenv
load_dotenv() 

import os
import json
from typing import List
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.settings import router as settings_router
from app.history import history_router
from app.llm import llm_router

# 创建FastAPI应用
app = FastAPI(title="测试用例辅助生成系统", description="基于用户故事的测试用例自动生成")
app.include_router(llm_router)
app.include_router(settings_router)
app.include_router(history_router)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据存储目录
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

@app.get("/")
async def root():
    return {"message": "测试用例辅助生成系统 API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("测试用例辅助生成系统启动中...")
    print("访问 http://localhost:8000 查看API文档")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)