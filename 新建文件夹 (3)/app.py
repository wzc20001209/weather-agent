import streamlit as st
import os
import uuid

# -------------------------- 1. 全局配置（禁用所有动态渲染） --------------------------
st.set_page_config(page_title="天气查询助手", layout="centered")
st.markdown("""
    <style>
    /* 完全重置Streamlit样式，杜绝DOM冲突 */
    * {box-sizing: border-box; margin: 0; padding: 0;}
    .stApp {background-color: #f0f2f6; padding-bottom: 100px !important;}
    .stButton>button {width: 100%; background-color: #2187ab; color: white; border: none; border-radius: 8px; padding: 0.8rem;}
    .stTextInput>div>input {width: 100%; padding: 0.8rem; border: 1px solid #ddd; border-radius: 8px;}
    /* 聊天消息样式 */
    .msg-user {background: #2187ab; color: white; padding: 1rem; border-radius: 12px 12px 0 12px; margin: 0.8rem 0; text-align: right; max-width: 80%; margin-left: auto;}
    .msg-assist {background: white; color: #333; padding: 1rem; border-radius: 12px 12px 12px 0; margin: 0.8rem 0; max-width: 80%; margin-right: auto;}
    .chat-container {max-height: 70vh; overflow-y: auto; padding: 1rem; background: #fff; border-radius: 12px; margin-bottom: 2rem;}
    </style>
""", unsafe_allow_html=True)

# -------------------------- 2. 初始化会话（仅用基础session_state，无复杂操作） --------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # 仅存消息列表，无其他动态key
if "submit_trigger" not in st.session_state:
    st.session_state.submit_trigger = False

# -------------------------- 3. 核心业务逻辑（和之前一致，无修改） --------------------------
def parse_intent(prompt):
    """替换为你的真实意图解析逻辑"""
    import re
    city_pattern = re.findall(r"([北京上海广州深圳成都杭州武汉重庆南京天津]+)", prompt)
    time_pattern = re.findall(r"(今天|未来3天|明天|后天)", prompt)
    return {
        "city": city_pattern[0] if city_pattern else "未指定",
        "time_range": time_pattern[0] if time_pattern else "今天"
    }

def get_weather(city, time_range):
    """替换为你的真实天气查询逻辑"""
    # 示例：返回模拟数据，替换为和风天气API调用
    return {
        "city": city,
        "time_range": time_range,
        "temp": "25℃",
        "desc": "晴转多云",
        "wind": "微风"
    }

def generate_answer(weather_data):
    """替换为你的真实回答生成逻辑"""
    return f"{weather_data['city']}{weather_data['time_range']}天气：\n🌡️ 温度：{weather_data['temp']}\n☁️ 状况：{weather_data['desc']}\n💨 风力：{weather_data['wind']}"

# -------------------------- 4. 页面渲染（纯静态，无动态DOM操作） --------------------------
# 标题
st.title("🌤️ 天气查询助手")

# 聊天记录展示（纯静态渲染，无任何动态操作）
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="msg-assist">{msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 输入区域（用表单提交，杜绝实时DOM操作）
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("请输入查询指令（如：北京今天天气）", key="user_input", placeholder="输入后点击提交...")
    submit_btn = st.form_submit_button(label="提交查询")

# -------------------------- 5. 提交处理（仅重载，无动态DOM修改） --------------------------
if submit_btn and user_input.strip():
    # 1. 添加用户消息
    st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
    
    # 2. 执行天气查询
    try:
        intent = parse_intent(user_input.strip())
        city = intent["city"]
        time_range = intent["time_range"]
        
        if city == "未指定":
            response = "😥 未识别到城市！请输入如「北京今天天气」的指令"
        else:
            weather_data = get_weather(city, time_range)
            response = generate_answer(weather_data)
    except Exception as e:
        response = f"⚠️ 查询失败：{str(e)}"
    
    # 3. 添加助手消息
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    
    # 4. 强制页面重载（核心：用页面重载代替动态DOM操作）
    st.experimental_set_query_params(refresh=uuid.uuid4())  # 触发URL变化，强制重载
    st.rerun()  # 兜底重载

# 清空聊天记录按钮
if st.button("🗑️ 清空聊天记录"):
    st.session_state.chat_history = []
    st.experimental_set_query_params(refresh=uuid.uuid4())
    st.rerun()
