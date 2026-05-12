import os
import json
from typing import List, Optional
from openai import OpenAI

class LLMGenerator:
    """LLM测试用例生成器"""
    
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))
        
        # 根据供应商选择API密钥和base_url
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = None
        elif self.provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            base_url = "https://api.deepseek.com/v1"
        elif self.provider == "qwen":
            api_key = os.getenv("DASHCOPE_API_KEY")          # 或 QWEN_API_KEY
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        else:
            raise ValueError(f"不支持的LLM提供商: {self.provider}")
        
        if not api_key:
            raise ValueError(f"请在.env中设置{self.provider.upper()}_API_KEY")
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    def generate_test_cases(self, user_story: str, acceptance_criteria: str = "", methods: Optional[List[str]] = None) -> List[dict]:
        """
        调用LLM生成测试用例，返回结构化的用例列表。
        返回格式与现有TestCase模型兼容的字典列表。
        """
        prompt = self._build_prompt(user_story, acceptance_criteria, methods)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的测试工程师，擅长根据用户故事生成详细的测试用例。"},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        content = response.choices[0].message.content
        # 尝试从返回内容中提取JSON
        test_cases = self._parse_response(content)
        return test_cases
    
    def _build_prompt(self, user_story: str, acceptance_criteria: str, methods: Optional[List[str]] = None) -> str:
        # 构建方法侧重说明
        method_note = ""
        if methods:
            method_list = "、".join(methods)
            method_note = f"\n- 请重点使用以下测试方法：{method_list}。\n"
            # 如果包含某些特殊方法，给出简短解释，帮助LLM理解
            if "状态迁移" in methods:
                method_note += "- 状态迁移法：分析业务状态转换路径，设计状态变化相关的用例。\n"
            if "错误推测" in methods:
                method_note += "- 错误推测法：基于经验猜测系统可能出错的地方进行测试。\n"
        
        prompt = f"""你是一名资深测试工程师，请根据以下用户故事和验收标准，设计全面的测试用例。请严格遵守以下规则：

    【用户故事】
    {user_story}

    【验收标准】
    {acceptance_criteria if acceptance_criteria else "未提供，请根据故事自行推导"}

    【生成要求】
    1. 所有内容必须使用**简体中文**（专业术语除外，如 ID、URL 等）
    2. 生成 **8～15 条**测试用例，覆盖正常流程、异常场景、边界条件；即使业务逻辑简单，也应通过不同测试方法生成至少8条
    3. 同时考虑以下维度（如适用）：
    - **安全测试**：未授权访问、SQL注入、XSS等
    - **性能测试**：大数据量、高并发、超时等
    - **兼容性测试**：不同浏览器、设备、屏幕分辨率
    - **可用性测试**：提示信息清晰度、操作流程顺畅性
    4. 优先级按 P0(最高)、P1、P2、P3 划分，并**按优先级从高到低排序**
    5. 每个用例必须包含：
    - id: 格式为 TC-LLM-XXX（如 TC-LLM-001）
    - title: 简洁描述测试目的
    - priority: P0/P1/P2/P3
    - test_method: 使用的测试方法（如等价类、边界值、场景法、状态迁移、错误推测、安全测试、性能测试等）
    - precondition: 测试前需满足的具体条件
    - steps: 列表，每个步骤包含 step_number(数字)、action(操作描述)、expected_result(预期结果)
    - tags: 标签数组（如 ["smoke", "回归"]）
    6. 步骤描述要**具体、可执行**，避免“输入有效值”这类模糊说法，应明确具体值
    7. 对于非法输入或异常场景，需写明预期的**错误提示信息**
    {method_note}
    8. 只返回纯 JSON 数组，不要带任何 markdown 代码块标记（如 ```json），也不要添加额外解释

    【输出示例】
    [
    {{
        "id": "TC-LLM-001",
        "title": "正确关键词搜索成功",
        "priority": "P1",
        "test_method": "等价类",
        "precondition": "用户已登录，位于搜索页",
        "steps": [
        {{"step_number": 1, "action": "在搜索框输入'手机'", "expected_result": "输入框正常接受"}},
        {{"step_number": 2, "action": "点击搜索按钮", "expected_result": "页面展示与'手机'相关的商品列表"}}
        ],
        "tags": ["功能测试", "冒烟"]
    }}
    ]

    现在，请开始生成测试用例："""
        return prompt
    
    def _parse_response(self, content: str) -> List[dict]:
        # 简单提取JSON，忽略可能包裹的```json```标记
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]
        try:
            test_cases = json.loads(content)
            if isinstance(test_cases, list):
                return test_cases
        except json.JSONDecodeError:
            pass
        # 解析失败，返回空列表或尝试手动修复
        return []