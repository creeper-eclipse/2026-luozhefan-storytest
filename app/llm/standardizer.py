import os
import json
from typing import List
from openai import OpenAI

class StoryStandardizer:
    """使用LLM将原始需求转化为标准用户故事和验收标准"""
    
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.temperature = 0.2  # 标准化任务用较低温度保证稳定
        
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
    
    def standardize(self, raw_text: str) -> List[dict]:
        """
        将复杂需求拆解为一个或多个标准用户故事，每个故事附带验收标准。
        返回: [{"user_story": "...", "acceptance_criteria": "..."}, ...]
        """
        prompt = f"""你是一个专业的需求分析师。请将以下原始需求拆解为一个或多个标准用户故事，每个故事都需附带验收标准。

原始需求：
{raw_text}

要求：
1. 如果需求简单，返回1个故事；如果需求复杂，允许返回2~5个独立的故事。
2. 每个故事必须严格遵守格式：作为 [角色]，我想要 [功能]，以便 [价值]。
3. 每个故事的验收标准以字符串形式给出，每条用数字编号，用 \\n 换行分隔，至少3条。
4. 整个输出必须是一个JSON数组，每个元素包含两个字段：'user_story' 和 'acceptance_criteria'。
5. 只输出JSON数组，不要任何其他内容。

示例输出：
[
  {{
    "user_story": "作为已注册用户，我想要通过手机验证码重置密码，以便在忘记密码时找回账号。",
    "acceptance_criteria": "1. 输入已注册手机号，点击获取验证码，收到6位数字验证码\\n2. 输入正确验证码后，可设置新密码\\n3. 验证码错误时，提示错误信息"
  }},
  {{
    "user_story": "作为管理员，我想要查看用户密码重置记录，以便审计安全事件。",
    "acceptance_criteria": "1. 管理员登录后台，可见重置记录列表\\n2. 记录包含手机号、时间、结果\\n3. 支持按时间范围筛选"
  }}
]"""
    
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的需求分析师，擅长编写用户故事和验收标准。"},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=1024
        )
        
        content = response.choices[0].message.content
        return self._parse_response(content)

    def _parse_response(self, content: str) -> List[dict]:
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines)
        try:
            data = json.loads(content)
            # 如果是对象（可能带user_story字段），转为列表
            if isinstance(data, dict):
                if "user_story" in data:
                    data = [data]
                else:
                    return []
            if isinstance(data, list):
                return [item for item in data if "user_story" in item]
        except json.JSONDecodeError:
            pass
        return []

# 创建单例（或每次新建，保持简单）
standardizer = StoryStandardizer()