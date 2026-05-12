import os
from typing import List
from fastapi import APIRouter
from pydantic import BaseModel
from app.llm.service import LLMGenerator
from app.history.manager import add_record
from app.llm.standardizer import standardizer
from app.llm.code_generator import code_generator
from typing import List, Optional

router = APIRouter(prefix="/generate", tags=["LLM生成"])

# ---------- 请求/响应模型 ----------
class LLMGenerateRequest(BaseModel):
    user_story: str
    acceptance_criteria: str = ""
    methods: Optional[List[str]] = None

class LLMGenerateResponse(BaseModel):
    success: bool
    test_cases: list = []
    message: str = ""

class StandardizeRequest(BaseModel):
    raw_text: str

class StoryItem(BaseModel):
    user_story: str
    acceptance_criteria: str

class StandardizeResponse(BaseModel):
    success: bool
    stories: List[StoryItem] = []
    message: str = ""

# ---------- 路由 ----------
@router.post("/llm", response_model=LLMGenerateResponse)
async def generate_with_llm(request: LLMGenerateRequest):
    """使用LLM生成测试用例（需先在.env中开启）"""
    if os.getenv("ENABLE_LLM_ENHANCEMENT", "false").lower() != "true":
        return LLMGenerateResponse(
            success=False,
            message="LLM增强功能未启用，请在.env中设置 ENABLE_LLM_ENHANCEMENT=true 并配置API密钥"
        )

    try:
        generator = LLMGenerator()
        test_cases = generator.generate_test_cases(
            request.user_story,
            request.acceptance_criteria,
            request.methods
        )

        for tc in test_cases:
            tc['source'] = 'llm'

        return LLMGenerateResponse(
            success=True,
            test_cases=test_cases,
            message=f"成功生成 {len(test_cases)} 个测试用例"
        )
    except Exception as e:
        try:
            add_record(
                type="testcase_failed",
                input_text=request.user_story,
                output_data={"error": str(e)}
            )
        except:
            pass  # 即使保存失败也不影响主流程
        return LLMGenerateResponse(
            success=False,
            message=f"LLM生成失败: {str(e)}"
        )


@router.post("/standardize", response_model=StandardizeResponse)
async def standardize_story(request: StandardizeRequest):
    """将原始需求转化为标准用户故事（可能拆解为多个），并生成验收标准"""
    if os.getenv("ENABLE_LLM_ENHANCEMENT", "false").lower() != "true":
        return StandardizeResponse(
            success=False,
            message="LLM增强功能未启用，请在.env中设置 ENABLE_LLM_ENHANCEMENT=true 并配置API密钥"
        )

    try:
        stories = standardizer.standardize(request.raw_text)
        if not stories:
            return StandardizeResponse(success=False, message="未能生成有效用户故事，请检查输入")
        return StandardizeResponse(
            success=True,
            stories=[StoryItem(**s) for s in stories],
            message=f"成功生成 {len(stories)} 个标准故事"
        )
    except Exception as e:
        return StandardizeResponse(
            success=False,
            message=f"标准化失败: {str(e)}"
        )

class CodeGenerateRequest(BaseModel):
    user_story: str
    acceptance_criteria: str = ""
    language: str = "Python"

class CodeGenerateResponse(BaseModel):
    success: bool
    code: str = ""
    message: str = ""

@router.post("/code", response_model=CodeGenerateResponse)
async def generate_code(request: CodeGenerateRequest):
    if os.getenv("ENABLE_LLM_ENHANCEMENT", "false").lower() != "true":
        return CodeGenerateResponse(success=False, message="LLM增强功能未启用")
    try:
        code = code_generator.generate_code(
            request.user_story,
            request.acceptance_criteria,
            request.language
        )
        if not code:
            return CodeGenerateResponse(success=False, message="生成失败")
        return CodeGenerateResponse(success=True, code=code, message="代码生成成功")
    except Exception as e:
        try:
            add_record(
                type="code_failed",
                input_text=request.user_story,
                output_data={"error": str(e)}
            )
        except:
            pass
        return CodeGenerateResponse(
            success=False,
            message=f"失败: {str(e)}"
        )