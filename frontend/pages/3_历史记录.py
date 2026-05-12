import streamlit as st
import requests
import json

st.set_page_config(page_title="历史记录", page_icon="📜", layout="wide")

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

st.title("📜 生成历史记录")

if 'api_url' not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"
api_url = st.session_state.api_url

with st.sidebar:
    st.header("📖 使用说明")
    st.markdown("""
    - 按**类型**和**日期范围**筛选生成记录
    - 展开记录查看详细内容
    - 可删除不需要的记录
    - 可将单个记录导出为 JSON 文件
    """)

type_display = {
    "standardize": "需求标准化",
    "testcase": "测试用例",
    "code": "代码",
    "testcase_failed": "测试用例(失败)",
    "code_failed": "代码(失败)"
}

# 从显示名称反向映射到 key
key_map = {v: k for k, v in type_display.items()}

# --- 筛选控件：类型 + 日期范围 ---
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    type_options = ["全部"] + list(type_display.values())
    type_filter = st.selectbox("类型筛选", type_options)
with col_f2:
    start_date = st.date_input("开始日期", value=None)
with col_f3:
    end_date = st.date_input("结束日期", value=None)

# 将用户选择的类型映射为后端需要的 key
filter_key = key_map.get(type_filter) if type_filter != "全部" else None

# 日期转为字符串（YYYY-MM-DD），若未选择则为 None
start_str = start_date.strftime("%Y-%m-%d") if start_date else None
end_str = end_date.strftime("%Y-%m-%d") if end_date else None

# 加载历史记录的函数（增加日期参数）
@st.cache_data(ttl=5)
def load_history(ftype=None, start=None, end=None):
    params = {}
    if ftype:
        params['type'] = ftype
    if start:
        params['start'] = start
    if end:
        params['end'] = end
    try:
        resp = requests.get(f"{api_url}/history", params=params, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except:
        return []

records = load_history(filter_key, start_str, end_str)

if not records:
    st.info("暂无记录")
else:
    # 初始化编辑用的 session_state
    for rec in records:
        if rec['type'] == 'standardize':
            stories = rec['output_data'].get('stories', [])
            for i, story in enumerate(stories):
                key_user = f"edit_user_{rec['id']}_{i}"
                key_ac = f"edit_ac_{rec['id']}_{i}"
                if key_user not in st.session_state:
                    st.session_state[key_user] = story['user_story']
                if key_ac not in st.session_state:
                    st.session_state[key_ac] = story['acceptance_criteria']
    for rec in records:
        with st.expander(f"{rec['created_at'][:19]} | {type_display.get(rec['type'], rec['type'])} | {rec['input_text'][:60]}..."):
            st.write(f"**类型**：{type_display.get(rec['type'], rec['type'])}")
            st.write(f"**时间**：{rec['created_at']}")
            st.write(f"**输入**：{rec['input_text']}")
            if rec['type'] == 'testcase':
                test_cases = rec['output_data'].get('test_cases', [])
                if test_cases:
                    # 统计信息（与主页类似，但简化）
                    col_tc1, col_tc2, col_tc3 = st.columns(3)
                    with col_tc1:
                        st.metric("总用例数", len(test_cases))
                    with col_tc2:
                        p0 = sum(1 for t in test_cases if t.get('priority') == 'P0')
                        st.metric("P0 用例", p0)
                    with col_tc3:
                        methods = set(t.get('test_method') for t in test_cases if t.get('test_method'))
                        st.metric("测试方法", len(methods))
                    st.markdown("---")
                    for tc in test_cases:
                        priority_color = {
                            'P0': '🔴', 'P1': '🟠', 'P2': '🟡', 'P3': '🟢'
                        }.get(tc.get('priority'), '⚪')
                        st.markdown(f"### {priority_color} {tc['id']} - {tc['title']} [{tc.get('priority', 'P2')}]")
                        st.markdown(f"**测试方法**: {tc.get('test_method', '-')}")
                        st.markdown(f"**前置条件**: {tc.get('precondition', '-')}")
                        st.markdown("**测试步骤:**")
                        for step in tc.get('steps', []):
                            st.markdown(f"{step['step_number']}. **操作**: {step['action']}")
                            st.markdown(f"   **预期**: {step['expected_result']}")
                        st.markdown("---")
            elif rec['type'] == 'standardize':
                stories = rec['output_data'].get('stories', [])
                # 使用表单包裹编辑区域和保存按钮
                with st.form(key=f"edit_form_{rec['id']}"):
                    updated_stories = []
                    for i, story in enumerate(stories):
                        st.markdown(f"**故事 {i+1}**")
                        new_user = st.text_area("用户故事", value=story['user_story'], height=80, key=f"edit_user_{rec['id']}_{i}")
                        new_ac = st.text_area("验收标准", value=story['acceptance_criteria'], height=120, key=f"edit_ac_{rec['id']}_{i}")
                        updated_stories.append({"user_story": new_user.strip(), "acceptance_criteria": new_ac.strip()})
                    
                    submitted = st.form_submit_button("💾 保存修改")
                    if submitted:
                        # 过滤掉空故事
                        valid_stories = [s for s in updated_stories if s['user_story']]
                        if not valid_stories:
                            st.error("请至少保留一个有效的用户故事。")
                        else:
                            try:
                                resp = requests.put(
                                    f"{api_url}/history/{rec['id']}",
                                    json={"output_data": {"stories": valid_stories}},
                                    timeout=5
                                )
                                if resp.status_code == 200:
                                    st.success("修改已保存！")
                                    # 更新本地数据，并清除缓存
                                    rec['output_data']['stories'] = valid_stories
                                    st.cache_data.clear()
                                    # 不再使用 st.rerun()，表单会自动重新运行脚本，但不会触发重复提交
                                else:
                                    st.error(f"保存失败: {resp.text}")
                            except Exception as e:
                                st.error(f"保存失败: {str(e)}")
            elif rec['type'] == 'code':
                # 显示输入的用户故事和验收标准（如果保存了）
                in_story = rec['output_data'].get('user_story', rec['input_text'])  # 兼容旧数据
                in_criteria = rec['output_data'].get('acceptance_criteria', '')
                st.markdown("📖 **输入用户故事**")
                st.code(in_story, language="text")
                if in_criteria:
                    st.markdown("✅ **验收标准**")
                    st.code(in_criteria, language="text")
                st.markdown("📄 **生成的代码**")
                st.code(rec['output_data'].get('code', ''))
            elif rec['type'] == 'testcase_failed':
                st.error("⚠️ 生成失败")
                st.text(f"错误信息：{rec['output_data'].get('error', '未知错误')}")
            elif rec['type'] == 'code_failed':
                st.error("⚠️ 代码生成失败")
                st.text(f"错误信息：{rec['output_data'].get('error', '未知错误')}")
            # 删除和导出按钮
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ 删除", key=f"del_{rec['id']}"):
                    if requests.delete(f"{api_url}/history/{rec['id']}").status_code == 200:
                        st.success("删除成功")
                        st.cache_data.clear()
                        st.rerun()
            with col2:
                st.download_button("下载 JSON", data=json.dumps(rec['output_data'], ensure_ascii=False, indent=2), file_name=f"hist_{rec['id']}.json")