from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime

# ============= 测试用例相关模型 =============
class TestStep(BaseModel):
    step_number: int
    action: str
    expected_result: str

class TestCase(BaseModel):
    """测试用例完整定义（LLM 生成）"""
    id: str
    title: str
    story_text: str = ""
    priority: str = "P2"                # 不再使用枚举，直接存储字符串 P0/P1/P2/P3
    test_method: Optional[str] = None   # 直接存储测试方法名称
    precondition: str = ""
    steps: List[TestStep] = Field(default_factory=list)
    postcondition: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    source: str = "llm"                # 固定为 llm，表示由大模型生成

    def to_dict(self):
        """自定义序列化方法，处理 datetime 和嵌套对象"""
        return {
            "id": self.id,
            "title": self.title,
            "story_text": self.story_text,
            "priority": self.priority,
            "test_method": self.test_method,
            "precondition": self.precondition,
            "steps": [step.dict() for step in self.steps],
            "postcondition": self.postcondition,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags,
            "source": self.source
        }

# ============= 请求/响应模型 =============
class GenerateRequest(BaseModel):
    user_story: str
    acceptance_criteria: str = ""

class GenerateResponse(BaseModel):
    success: bool
    test_cases: List[TestCase] = Field(default_factory=list)
    message: str = ""