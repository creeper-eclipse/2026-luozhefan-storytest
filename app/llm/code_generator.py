import os
from typing import Optional
from openai import OpenAI

class CodeGenerator:
    """LLM 代码生成器"""

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.temperature = 0.3
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))

        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = None
        elif self.provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            base_url = "https://api.deepseek.com/v1"
        elif self.provider == "qwen":
            api_key = os.getenv("DASHCOPE_API_KEY")
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        else:
            raise ValueError(f"不支持的LLM提供商: {self.provider}")

        if not api_key:
            raise ValueError(f"请在.env中设置{self.provider.upper()}_API_KEY")

        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate_code(self, user_story: str, acceptance_criteria: str = "", language: str = "Python") -> str:
        prompt = self._build_prompt(user_story, acceptance_criteria, language)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个资深软件工程师，只输出代码，不含其他文字。"},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        content = response.choices[0].message.content
        return self._clean_code(content)

    def _build_prompt(self, user_story: str, acceptance_criteria: str, language: str) -> str:
        return f"""请根据以下用户故事和验收标准生成 {language} 代码。要求：
- 实现验收标准中的所有功能
- 代码包含必要的函数/类定义
- 适当添加注释
- 只输出代码，不要任何对话文字或代码块标记

【用户故事】
{user_story}

【验收标准】
{acceptance_criteria if acceptance_criteria else "未提供"}"""

    def _clean_code(self, content: str) -> str:
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines)
        return content

# 全局单例
code_generator = CodeGenerator()