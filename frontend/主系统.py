import streamlit as st
import requests
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="测试用例辅助生成系统",
    page_icon="🧪",
    layout="wide"
)

# 注入自定义CSS，美化侧边栏和主区域
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

st.title("🧪 基于用户故事的测试用例辅助生成系统")
st.markdown("---")

# 侧边栏现在只用于导航，不再放配置和格式说明
# Streamlit 自动根据 pages/ 生成导航，无需额外内容
# 但为保留使用说明，我们放入一个可折叠区域
with st.sidebar:
    st.header("📖 使用说明")
    st.markdown("""
    1. 输入用户故事（标准格式）
    2. 可选：输入验收标准
    3. 选择测试设计方法
    4. 点击生成按钮
    5. 导出测试用例
    """)

# 获取API地址（从设置页面共享的 session_state）
if 'api_url' not in st.session_state:
    st.session_state.api_url = os.getenv("API_URL", "http://localhost:8000")
api_url = st.session_state.api_url


st.subheader("📝 输入")

user_story = st.text_area(
    "用户故事",
     height=150,
    placeholder="例如：作为普通用户，我想要使用手机号+密码登录，以便访问我的个人数据"
)

acceptance_criteria = st.text_area(
    "验收标准（可选）",
    height=100,
    placeholder="例如：\n1. 输入正确的手机号和密码，登录成功\n2. ..."
)

test_methods = st.multiselect(
    "🧪 测试方法侧重（可选）",
    ["等价类", "边界值", "场景法", "状态迁移", "错误推测", "安全测试", "性能测试"],
    default=["等价类", "边界值", "场景法"],
    help="选择希望AI重点使用的测试方法。不选则使用默认范围。"
)

generate_btn = st.button("🚀 生成测试用例", type="primary", use_container_width=True)
        
# 生成逻辑（保持不变）
if generate_btn:
    if not user_story:
        st.error("请填写用户故事")
    else:
        with st.spinner("正在使用AI生成测试用例（约10~30秒）..."):
            try:
                response = requests.post(f"{api_url}/generate/llm", json={
                    "user_story": user_story,
                    "acceptance_criteria": acceptance_criteria,
                    "methods": test_methods
                }, timeout=120)
                if response.status_code == 200:
                    result = response.json()
                    if result['success']:
                        st.session_state['test_cases'] = result['test_cases']
                        st.success(result['message'])
                        # 保存历史
                        try:
                            requests.post(f"{api_url}/history", json={
                                "type": "testcase",
                                "input_text": user_story,
                                "output_data": {
                                    "test_cases": result['test_cases'],
                                    "acceptance_criteria": acceptance_criteria
                                }
                            }, timeout=5)
                        except:
                            pass
                    else:
                        st.error(result['message'])
                else:
                    st.error(f"API错误: {response.status_code}")
            except Exception as e:
                st.error(f"请求失败: {str(e)}")

# 显示生成的测试用例（保持不变）
if 'test_cases' in st.session_state and st.session_state['test_cases']:
    st.markdown("---")
    st.subheader("📋 生成的测试用例")
    test_cases = st.session_state['test_cases']

    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("总用例数", len(test_cases))
    with col_stat2:
        p0_count = sum(1 for tc in test_cases if tc.get('priority') == 'P0')
        st.metric("P0用例", p0_count)
    with col_stat3:
        p1_count = sum(1 for tc in test_cases if tc.get('priority') == 'P1')
        st.metric("P1用例", p1_count)
    with col_stat4:
        methods_used = set(tc.get('test_method') for tc in test_cases if tc.get('test_method'))
        st.metric("使用方法", len(methods_used))

    for tc in test_cases:
        priority_color = {
            'P0': '🔴', 'P1': '🟠', 'P2': '🟡', 'P3': '🟢'
        }.get(tc.get('priority'), '⚪')
        source = tc.get('source', 'rule')
        source_label = "🤖 LLM" if source == "llm" else "📋 规则"
        with st.expander(f"{priority_color} {source_label} {tc['id']} - {tc['title']} [{tc.get('priority', 'P2')}]"):
            st.markdown(f"**测试方法**: {tc.get('test_method', '-')}")
            st.markdown(f"**前置条件**: {tc.get('precondition', '-')}")
            st.markdown("**测试步骤:**")
            for step in tc.get('steps', []):
                st.markdown(f"{step['step_number']}. **操作**: {step['action']}")
                st.markdown(f"   **预期**: {step['expected_result']}")

    st.markdown("---")
    st.subheader("💾 导出")
    col_export1, col_export2, col_export3 = st.columns(3)
    with col_export1:
        if st.button("📄 导出为JSON", use_container_width=True):
            export_data = {
                "generated_at": datetime.now().isoformat(),
                "test_cases": test_cases
            }
            st.download_button(
                label="下载JSON",
                data=json.dumps(export_data, ensure_ascii=False, indent=2),
                file_name=f"test_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    with col_export2:
        if st.button("📊 导出为CSV", use_container_width=True):
            csv_lines = ["用例ID,标题,优先级,测试方法,前置条件,步骤,预期结果"]
            for tc in test_cases:
                steps_str = "\\n".join([f"{s['step_number']}.{s['action']}" for s in tc.get('steps', [])])
                expected_str = "\\n".join([f"{s['step_number']}.{s['expected_result']}" for s in tc.get('steps', [])])
                csv_lines.append(f"{tc['id']},{tc['title']},{tc.get('priority','')},{tc.get('test_method','')},{tc.get('precondition','')},{steps_str},{expected_str}")
            st.download_button(
                label="下载CSV",
                data="\n".join(csv_lines).encode('utf-8-sig'),
                file_name=f"test_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    with col_export3:
        if st.button("📝 导出为Markdown", use_container_width=True):
            # 构建 Markdown 内容
            md = f"# 测试用例\n\n"
            md += f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            md += f"共 {len(test_cases)} 个测试用例\n\n"

            for tc in test_cases:
                md += f"## {tc['id']} - {tc['title']}\n\n"
                md += f"- **优先级**：{tc.get('priority', '')}\n"
                md += f"- **测试方法**：{tc.get('test_method', '-')}\n"
                md += f"- **前置条件**：{tc.get('precondition', '-')}\n\n"
                md += "### 测试步骤\n\n"
                md += "| 步骤 | 操作 | 预期结果 |\n"
                md += "|------|------|----------|\n"
                for step in tc.get('steps', []):
                    md += f"| {step['step_number']} | {step['action']} | {step['expected_result']} |\n"
                md += "\n---\n\n"

            st.download_button(
                label="下载Markdown",
                data=md.encode('utf-8'),
                file_name=f"test_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )