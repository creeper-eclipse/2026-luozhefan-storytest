import streamlit as st
import requests
import os

st.set_page_config(
    page_title="系统设置",
    page_icon="⚙️",
    layout="wide"
)

# 注入侧边栏美化样式
st.markdown("""
<style>
    /* ---------- 导航链接通用样式：白底黑字 ---------- */
    [data-testid="stSidebarNav"] a,
    [data-testid="stSidebarNav"] button,
    [data-testid="stSidebarNav"] a:link,
    [data-testid="stSidebarNav"] a:visited,
    [data-testid="stSidebarNav"] a:hover,
    [data-testid="stSidebarNav"] a:active {
        display: block !important;
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        padding: 0.6rem 1rem !important;
        margin: 0.2rem 0.5rem 0.5rem 0.5rem !important;
        border-radius: 0.5rem !important;
        text-decoration: none !important;
        
        /* 白底黑字 */
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        
        transition: none !important;   /* 悬停无动画变化 */
    }

    /* 取消悬停时的任何样式变化 */
    [data-testid="stSidebarNav"] a:hover,
    [data-testid="stSidebarNav"] button:hover {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }

    /* 主内容区可选样式 */
    .main .block-container {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚙️ 系统设置")
st.markdown("在此配置后端 API 连接和 LLM 大模型参数，修改后需**重启后端服务**才能生效。")

# 获取当前 API 地址（与主页共享）
if 'api_url' not in st.session_state:
    st.session_state.api_url = os.getenv("API_URL", "http://localhost:8000")
api_url = st.session_state.api_url

with st.sidebar:
    st.header("📖 使用说明")
    st.markdown("""
    - 修改 **API 地址** 或 **LLM 参数** 后点击“保存配置”
    - 更改将写入 `.env` 文件，需**重启后端服务**才能生效
    - API 密钥请妥善保管
    """)

# 从后端获取当前配置（首次加载）
@st.cache_data(ttl=10)
def get_settings():
    try:
        resp = requests.get(f"{api_url}/settings", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return None

if 'settings_data' not in st.session_state:
    st.session_state.settings_data = get_settings()

# 如果获取失败，使用默认值
current = st.session_state.settings_data or {
    "api_host": "0.0.0.0",
    "api_port": 8000,
    "openai_api_key": "",
    "deepseek_api_key": "",
    "dashscope_api_key": "",
    "enable_llm": True,
    "llm_provider": "qwen",
    "llm_model": "qwen-max",
    "llm_temperature": 0.3,
    "llm_max_tokens": 4096
}

with st.form("settings_form"):
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🌐 后端服务")
        api_host = st.text_input("API Host", value=current.get("api_host", "0.0.0.0"))
        api_port = st.number_input("API Port", value=current.get("api_port", 8000), min_value=1024, max_value=65535)

        # 更新前端使用的 API 地址
        new_api_url = f"http://{api_host}:{api_port}"
        if new_api_url != api_url:
            st.session_state.api_url = new_api_url

    with col_right:
        st.subheader("🤖 LLM 大模型配置")
        llm_provider = st.selectbox(
            "提供商", 
            ["openai", "deepseek", "qwen"],
            index=["openai", "deepseek", "qwen"].index(current.get("llm_provider", "qwen"))
        )
        llm_model = st.text_input("模型名称", value=current.get("llm_model", "qwen-max"))
        llm_temperature = st.slider("温度 (Temperature)", 0.0, 2.0, float(current.get("llm_temperature", 0.3)), 0.1)
        llm_max_tokens = st.number_input("最大 Token 数", value=current.get("llm_max_tokens", 4096), min_value=256, max_value=32768)
        enable_llm = st.checkbox("启用 LLM 增强", value=current.get("enable_llm", True))

    st.subheader("🔑 API 密钥")
    openai_key = st.text_input("OpenAI API Key", value=current.get("openai_api_key", ""), type="password")
    deepseek_key = st.text_input("DeepSeek API Key", value=current.get("deepseek_api_key", ""), type="password")
    dashscope_key = st.text_input("DashScope API Key (千问)", value=current.get("dashscope_api_key", ""), type="password")

    submitted = st.form_submit_button("💾 保存配置", type="primary", use_container_width=True)

    if submitted:
        # 构建发送到后端的数据
        settings = {
            "api_host": api_host,
            "api_port": api_port,
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "llm_temperature": llm_temperature,
            "llm_max_tokens": llm_max_tokens,
            "enable_llm": enable_llm,
            "openai_api_key": openai_key,
            "deepseek_api_key": deepseek_key,
            "dashscope_api_key": dashscope_key
        }
        try:
            resp = requests.post(f"{api_url}/settings", json=settings, timeout=10)
            if resp.status_code == 200:
                st.success("配置已保存到 .env 文件！请重启后端服务使配置生效。")
                # 清除缓存，以便下次获取最新配置
                st.cache_data.clear()
            else:
                st.error(f"保存失败：{resp.text}")
        except requests.exceptions.ConnectionError:
            st.error(f"无法连接到后端服务 ({api_url})，请确认后端已启动。")