import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(
    page_title="AI需求标准化",
    page_icon="🤖",
    layout="wide"
)

# ---------- 自定义导航样式（白底黑字）----------
st.markdown("""
<style>
    [data-testid="stSidebarNav"] a, [data-testid="stSidebarNav"] button,
    [data-testid="stSidebarNav"] a:link, [data-testid="stSidebarNav"] a:visited,
    [data-testid="stSidebarNav"] a:hover, [data-testid="stSidebarNav"] a:active {
        display: block !important;
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        padding: 0.6rem 1rem !important;
        margin: 0.2rem 0.5rem 0.5rem 0.5rem !important;
        border-radius: 0.5rem !important;
        text-decoration: none !important;
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        transition: none !important;
    }
    [data-testid="stSidebarNav"] a:hover, [data-testid="stSidebarNav"] button:hover {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }
    .main .block-container {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 AI 需求标准化")
st.markdown("将自由文本转变为标准用户故事与验收标准，支持复杂需求拆解。")

# ---- 获取与主页同步的 API 地址 ----
if 'api_url' not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"
api_url = st.session_state.api_url

with st.sidebar:
    st.header("📖 使用说明")
    st.markdown("""
    1. 输入你的原始业务需求，不限格式
    2. 点击“生成标准故事”按钮
    3. AI 将拆解需求为**标准用户故事**和**验收标准**
    4. 可导出为 JSON / CSV / Markdown
    """)

# ---- 输入区域 ----
st.subheader("📝 原始需求描述")
raw_requirement = st.text_area(
    "输入您的需求描述，不限格式",
    height=250,
    placeholder="例如：我们需要一个用户管理后台，管理员可以查看、编辑、禁用用户。"
)
generate_btn = st.button("🎯 生成标准故事", type="primary", use_container_width=True)

# ---- 标准化结果区域 ----
st.subheader("📋 标准化结果")

# 初始占位提示（仅在没有任何生成结果时显示）
if 'standardized_stories' not in st.session_state:
    st.markdown("""
    <div style="border-left: 2px solid #e0e0e0; padding-left: 20px; margin-top: 20px;">
        <p style="color: #666;">👈 请先输入原始需求，然后点击“生成标准故事”。</p>
        <p style="color: #888; font-size: 0.9em;">AI 拆解的标准故事和验收标准将出现在此区域。</p>
    </div>
    """, unsafe_allow_html=True)
else:
    # 已有生成故事时，直接展示（避免重复渲染）
    pass

# ---- 生成逻辑 ----
if generate_btn:
    if not raw_requirement:
        st.warning("请先输入原始需求描述")
    else:
        with st.spinner("AI 正在拆解需求并生成标准故事..."):
            try:
                resp = requests.post(
                    f"{api_url}/generate/standardize",
                    json={"raw_text": raw_requirement},
                    timeout=60
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('success'):
                        stories = data.get('stories', [])
                        if stories:
                            st.session_state['standardized_stories'] = stories
                            st.success(f"成功生成 {len(stories)} 个标准故事")
                            # 保存历史
                            try:
                                requests.post(f"{api_url}/history", json={
                                    "type": "standardize",
                                    "input_text": raw_requirement,
                                    "output_data": {"stories": stories}
                                }, timeout=5)
                            except:
                                pass
                        else:
                            st.error("未能生成有效故事，请调整输入后重试。")
                    else:
                        st.error(data.get('message', '标准化失败'))
                else:
                    st.error(f"API 错误: {resp.status_code}")
            except requests.exceptions.ConnectionError:
                st.error(f"无法连接到后端服务 ({api_url})，请确保后端已启动。")
            except Exception as e:
                st.error(f"请求失败: {str(e)}")

# ---- 持久化展示 + 导出功能 ----
if 'standardized_stories' in st.session_state and st.session_state['standardized_stories']:
    stories = st.session_state['standardized_stories']
    # 展示每条故事
    for i, story in enumerate(stories):
        with st.expander(f"故事 {i+1}: {story['user_story'][:60]}...", expanded=(i==0)):
            st.markdown("**📖 用户故事**")
            st.code(story['user_story'], language="text")
            st.markdown("**✅ 验收标准**")
            st.code(story['acceptance_criteria'], language="text")

    # 导出功能
    st.markdown("---")
    st.subheader("💾 导出故事")
    col_exp1, col_exp2, col_exp3 = st.columns(3)

    with col_exp1:
        if st.button("📄 导出为JSON", use_container_width=True):
            export_data = {
                "generated_at": datetime.now().isoformat(),
                "stories": stories
            }
            st.download_button(
                label="下载JSON",
                data=json.dumps(export_data, ensure_ascii=False, indent=2),
                file_name=f"stories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    with col_exp2:
        if st.button("📊 导出为CSV", use_container_width=True):
            csv_lines = ["故事编号,用户故事,验收标准"]
            for idx, s in enumerate(stories, 1):
                us = s['user_story'].replace('\n', ' ')
                ac = s['acceptance_criteria'].replace('\n', ' ')
                csv_lines.append(f"{idx},{us},{ac}")
            st.download_button(
                label="下载CSV",
                data="\n".join(csv_lines).encode('utf-8-sig'),
                file_name=f"stories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    with col_exp3:
        if st.button("📝 导出为Markdown", use_container_width=True):
            md = f"# 需求标准化故事\n\n生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            for idx, s in enumerate(stories, 1):
                md += f"## 故事 {idx}\n\n"
                md += f"**用户故事**：{s['user_story']}\n\n"
                md += f"**验收标准**：\n\n{s['acceptance_criteria']}\n\n---\n\n"
            st.download_button(
                label="下载Markdown",
                data=md.encode('utf-8'),
                file_name=f"stories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )