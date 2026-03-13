import streamlit as st
import uuid  # 用于生成唯一key，彻底避免DOM冲突

# -------------------------- 1. 初始化配置（关键：禁用自动组件重渲染） --------------------------
st.set_page_config(page_title="天气查询助手", layout="wide")
if "messages" not in st.session_state:
    st.session_state.messages = []
if "input_key" not in st.session_state:
    st.session_state.input_key = str(uuid.uuid4())  # 每次刷新生成新key，避免缓存冲突

# -------------------------- 2. 自定义聊天样式（完全脱离Streamlit内置chat组件） --------------------------
def custom_chat_style():
    st.markdown("""
    <style>
    /* 隐藏Streamlit默认样式，减少干扰 */
    .stTextInput > div > div {border: none;}
    .main > div {padding-top: 1rem;}
    
    /* 聊天容器 */
    .chat-box {
        height: 70vh;
        overflow-y: auto;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    /* 用户消息 */
    .user-message {
        display: flex;
        justify-content: flex-end;
        margin: 0.5rem 0;
    }
    .user-message > div {
        background-color: #007bff;
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 0 18px;
        max-width: 70%;
    }
    
    /* 助手消息 */
    .assistant-message {
        display: flex;
        justify-content: flex-start;
        margin: 0.5rem 0;
    }
    .assistant-message > div {
        background-color: #e9ecef;
        color: #333;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 18px 0;
        max-width: 70%;
    }
    
    /* 输入框样式 */
    .input-container {
        position: fixed;
        bottom: 2rem;
        width: 80%;
        z-index: 999;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------------- 3. 自定义消息渲染函数（无DOM操作） --------------------------
def render_chat_message(role, content):
    """渲染单条消息，完全绕过Streamlit的chat组件"""
    if role == "user":
        st.markdown(f"""
        <div class="user-message">
            <div>{content}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="assistant-message">
            <div>{content}</div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------- 4. 模拟你的业务函数（替换为真实函数即可） --------------------------
# 请替换为你真实的 parse_intent/get_weather/generate_answer
def parse_intent(prompt, api_key, llm_type):
    """模拟意图解析"""
    import re
    city_pattern = re.findall(r"([北京上海广州深圳成都杭州武汉重庆南京天津]+)", prompt)
    time_pattern = re.findall(r"(今天|未来3天|明天|后天)", prompt)
    return {
        "city": city_pattern[0] if city_pattern else "未指定",
        "time_range": time_pattern[0] if time_pattern else "今天"
    }

def get_weather(city, time_range, qweather_key):
    """模拟获取天气数据"""
    return {
        "city": city,
        "time_range": time_range,
        "temp": "25℃",
        "desc": "晴转多云",
        "wind": "微风"
    }

def generate_answer(weather_data):
    """模拟生成回答"""
    return f"""
    {weather_data['city']}{weather_data['time_range']}天气：
    🌡️ 温度：{weather_data['temp']}
    ☁️ 状况：{weather_data['desc']}
    💨 风力：{weather_data['wind']}
    """

# -------------------------- 5. 主逻辑（无任何chat组件） --------------------------
# 注入样式
custom_chat_style()

# 聊天区域（固定容器，避免DOM重排）
st.subheader("天气查询助手")
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-box" id="chat-box">', unsafe_allow_html=True)
    # 渲染所有历史消息
    for msg in st.session_state.messages:
        render_chat_message(msg["role"], msg["content"])
    st.markdown('</div>', unsafe_allow_html=True)

# 输入区域（用原生text_input，且每次发送后重置key）
input_col, btn_col = st.columns([9, 1])
with input_col:
    user_input = st.text_input(
        "请输入查询指令（如：北京今天天气）",
        key=st.session_state.input_key,  # 唯一key避免DOM冲突
        placeholder="输入后点击发送按钮...",
        label_visibility="collapsed"
    )

with btn_col:
    send_btn = st.button("发送", use_container_width=True)

# 处理发送逻辑（核心：无实时渲染，仅更新session_state后刷新）
if send_btn and user_input.strip():
    # 1. 添加用户消息
    st.session_state.messages.append({
        "role": "user",
        "content": user_input.strip()
    })
    
    # 2. 天气查询逻辑（你的核心代码，无需修改）
    try:
        # 替换为你的真实参数
        LLM_API_KEY = "your_key"
        LLM_TYPE = "your_type"
        QWEATHER_KEY = "your_weather_key"
        
        intent = parse_intent(user_input, LLM_API_KEY, LLM_TYPE)
        city = intent["city"]
        time_range = intent["time_range"]
        
        if city == "未指定":
            response = "😥 未识别到城市！请输入如「北京今天天气」的指令"
        else:
            weather_data = get_weather(city, time_range, QWEATHER_KEY)
            response = generate_answer(weather_data)
    
    except Exception as e:
        response = f"⚠️ 查询失败：{str(e)}"
    
    # 3. 添加助手消息
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })
    
    # 4. 重置输入框（生成新key，彻底清空，避免DOM残留）
    st.session_state.input_key = str(uuid.uuid4())
    
    # 5. 强制刷新页面（让新消息渲染，无DOM操作）
    st.experimental_rerun()  # 低版本Streamlit用：st.experimental_rerun()

# 可选：清空聊天记录按钮
if st.button("清空聊天记录", type="secondary"):
    st.session_state.messages = []
    st.experimental_rerun()
