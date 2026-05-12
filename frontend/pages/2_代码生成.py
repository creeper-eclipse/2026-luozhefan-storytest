import streamlit as st
import requests

st.set_page_config(page_title="代码生成", page_icon="💻", layout="wide")

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

st.title("💻 AI 代码生成")

if 'api_url' not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"
api_url = st.session_state.api_url

with st.sidebar:
    st.header("📖 使用说明")
    st.markdown("""
    1. 填写**用户故事**（必填）和**验收标准**（可选）
    2. 选择目标编程语言
    3. 点击“生成代码”按钮
    4. AI 将根据需求生成相应功能的代码
    5. 可复制或下载代码文件
    """)

st.subheader("📝 输入")
user_story = st.text_area("用户故事", height=150)
acceptance_criteria = st.text_area("验收标准（可选）", height=100)
language = st.selectbox("语言", ["Python", "JavaScript", "Java", "TypeScript", "Go", "C", "C++"], index=0)
generate_btn = st.button("🚀 生成代码", type="primary", use_container_width=True)

if generate_btn:
    if not user_story:
        st.error("请填写用户故事")
    else:
        with st.spinner("AI 正在编写代码..."):
            try:
                resp = requests.post(f"{api_url}/generate/code", json={
                    "user_story": user_story,
                    "acceptance_criteria": acceptance_criteria,
                    "language": language
                }, timeout=120)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('success'):
                        st.session_state['generated_code'] = data['code']
                        st.success("代码生成成功")
                        # 保存历史
                        try:
                            requests.post(f"{api_url}/history", json={
                                "type": "code",
                                "input_text": user_story,
                                "output_data": {
                                    "code": data['code'],
                                    "user_story": user_story,
                                    "acceptance_criteria": acceptance_criteria
                                }
                            }, timeout=5)
                        except:
                            pass
                    else:
                        st.error(data.get('message'))
                else:
                    st.error(f"API错误: {resp.status_code}")
            except Exception as e:
                st.error(f"请求失败: {str(e)}")

if 'generated_code' in st.session_state and st.session_state['generated_code']:
    st.subheader("📄 生成的代码")
    st.code(st.session_state['generated_code'], language=language.lower())
    
    # 定义扩展名映射
    ext_map = {
        "Python": "py",
        "JavaScript": "js",
        "Java": "java",
        "TypeScript": "ts",
        "Go": "go",
        "C": "c",
        "C++": "cpp"
    }
    file_ext = ext_map.get(language, "txt")
    
    st.download_button("下载代码", data=st.session_state['generated_code'], file_name=f"code.{file_ext}")