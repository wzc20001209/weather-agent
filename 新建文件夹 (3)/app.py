import streamlit as st
import json
import requests
from datetime import datetime
import os

# ===================== 页面基础配置 =====================
st.set_page_config(
    page_title="豆包天气智能体",
    page_icon="🌤️",
    layout="centered"
)

# 侧边栏：API Key 配置
with st.sidebar:
    st.title("🔧 配置项")
    QWEATHER_KEY = st.text_input("和风天气 API Key", type="password", value=os.getenv("QWEATHER_KEY", ""))
    LLM_API_KEY = st.text_input("大模型 API Key（OpenAI/智谱）", type="password", value=os.getenv("LLM_API_KEY", ""))
    LLM_TYPE = st.selectbox("大模型类型", ["openai", "zhipu"], index=0)

# 主页面标题
st.title("🌤️ 豆包天气智能体")
st.caption("支持自然语言查询全国城市天气 | 基于 Streamlit Cloud 部署")

# ===================== 初始化会话状态（优化版） =====================
if "messages" not in st.session_state:
    st.session_state.messages = []  # 统一用 messages 命名，避免冲突

# ===================== 核心工具函数（保持不变） =====================
def parse_intent(user_input, llm_api_key, llm_type):
    prompt = f"""
    请严格按照JSON格式解析用户的天气查询指令，仅返回JSON，无其他内容：
    {{
        "city": "城市名（未指定则填'未指定'）",
        "time_range": "时间范围（今天/明天/未来3天/本周，默认今天）"
    }}
    用户输入：{user_input}
    """
    try:
        if llm_type == "openai":
            import openai
            openai.api_key = llm_api_key
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            intent = json.loads(response.choices[0].message.content)
        elif llm_type == "zhipu":
            from zhipuai import ZhipuAI
            zhipu_client = ZhipuAI(api_key=llm_api_key)
            response = zhipu_client.chat.completions.create(
                model="glm-3-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            intent = json.loads(response.choices[0].message.content)
        return intent
    except Exception as e:
        st.error(f"意图解析失败：{str(e)}")
        return {"city": "未指定", "time_range": "今天"}

def get_city_loc(city, qweather_key):
    if not qweather_key:
        st.error("请先配置和风天气 API Key！")
        return None
    url = f"https://geoapi.qweather.com/v2/city/lookup?location={city}&key={qweather_key}"
    try:
        resp = requests.get(url).json()
        if resp["code"] == "200" and resp["location"]:
            return {
                "lon": resp["location"][0]["lon"],
                "lat": resp["location"][0]["lat"],
                "name": resp["location"][0]["name"]
            }
        else:
            st.warning(f"未找到「{city}」的地理信息")
            return None
    except Exception as e:
        st.error(f"城市定位失败：{str(e)}")
        return None

def get_weather(city, time_range, qweather_key):
    loc = get_city_loc(city, qweather_key)
    if not loc:
        return {"error": f"未找到「{city}」的天气信息"}
    
    if time_range in ["今天", "未指定"]:
        url = f"https://devapi.qweather.com/v7/weather/now?location={loc['lon']},{loc['lat']}&key={qweather_key}"
        resp = requests.get(url).json()
        if resp["code"] == "200":
            return {
                "city": loc["name"],
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "temp": resp["now"]["temp"],
                "feels_like": resp["now"]["feelsLike"],
                "weather": resp["now"]["text"],
                "wind": f"{resp['now']['windDir']}{resp['now']['windScale']}级",
                "type": "today"
            }
    elif time_range == "未来3天":
        url = f"https://devapi.qweather.com/v7/weather/3d?location={loc['lon']},{loc['lat']}&key={qweather_key}"
        resp = requests.get(url).json()
        if resp["code"] == "200":
            data = []
            for day in resp["daily"]:
                data.append({
                    "date": day["fxDate"],
                    "temp_min": day["tempMin"],
                    "temp_max": day["tempMax"],
                    "weather": day["textDay"],
                    "wind": f"{day['windDirDay']}{day['windScaleDay']}级"
                })
            return {"city": loc["name"], "type": "3days", "data": data}
    return {"error": "暂不支持该时间范围查询（仅支持今天/未来3天）"}

def generate_answer(weather_data):
    if "error" in weather_data:
        return weather_data["error"]
    if weather_data["type"] == "today":
        answer = f"""
### 【{weather_data['city']} 实时天气】
⏰ 更新时间：{weather_data['time']}
🌡️ 实时温度：{weather_data['temp']}℃（体感 {weather_data['feels_like']}℃）
☁️ 天气状况：{weather_data['weather']}
💨 风向风力：{weather_data['wind']}
        """
    elif weather_data["type"] == "3days":
        answer = f"### 【{weather_data['city']} 未来3天天气】\n"
        for day in weather_data["data"]:
            answer += f"""
📅 **{day['date']}**：{day['weather']}
温度：{day['temp_min']}~{day['temp_max']}℃ | 风力：{day['wind']}
            """
    return answer.strip()

# ===================== 重构聊天交互逻辑（关键修复） =====================
# 1. 渲染历史消息（稳定版写法）
for msg in st.session_state.messages:
    with import streamlit as st  # 初始化聊天历史（session_state 保存对话记录） if "chat_history" not in st.session_state:     st.session_state.chat_history = []  # 自定义聊天样式（通过 markdown 注入 CSS，美化气泡样式） def inject_chat_css():     st.markdown("""     <style>     /* 整体聊天容器 */     .chat-container {         margin: 10px 0;     }     /* 用户消息气泡 */     .user-message {         background-color: #262730;         color: white;         padding: 12px 18px;         border-radius: 18px;         margin: 8px 0;         max-width: 70%;         margin-left: auto;         text-align: right;     }     /* 助手（AI）消息气泡 */     .assistant-message {         background-color: #37384f;         color: white;         padding: 12px 18px;         border-radius: 18px;         margin: 8px 0;         max-width: 70%;         margin-right: auto;     }     /* 消息头像/标签 */     .message-role {         font-size: 12px;         opacity: 0.7;         margin-bottom: 4px;     }     /* 输入框样式（可选） */     .stTextInput>div>div>input {         border-radius: 20px;         padding: 10px 16px;     }     </style>     """, unsafe_allow_html=True)  # 渲染单条消息（核心函数：模拟 chat_message 效果） def render_message(role, content):     """     role: 消息角色（user/assistant）     content: 消息内容     """     # 定义角色名称和样式类     role_name = "你" if role == "user" else "AI助手"     style_class = "user-message" if role == "user" else "assistant-message"          # 渲染单条消息（容器+头像标签+气泡内容）     with st.container():         st.markdown(f"""         <div class="chat-container">             <div class="message-role">{role_name}</div>             <div class="{style_class}">{content}</div>         </div>         """, unsafe_allow_html=True)  # 1. 注入自定义样式 inject_chat_css()  # 2. 渲染聊天历史 st.subheader("聊天界面（模拟版）") chat_container = st.container()  # 聊天历史容器（固定位置，避免刷新闪烁） with chat_container:     for msg in st.session_state.chat_history:         render_message(msg["role"], msg["content"])  # 3. 输入框（模拟聊天输入） user_input = st.text_input("请输入消息：", placeholder="输入后按回车发送...", key="user_input")  # 4. 处理发送逻辑 if user_input and user_input.strip():     # 添加用户消息到历史     st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})     # 模拟AI回复（替换为你的实际业务逻辑，比如调用LLM）     ai_reply = f"已收到你的消息：{user_input.strip()}（这是模拟回复）"     # 添加AI消息到历史     st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})     # 清空输入框（关键：通过 rerun 刷新页面+清空输入）     st.session_state.user_input = ""     st.rerun()  # 刷新页面，实时显示新消息  # 可选：清空聊天记录按钮 if st.button("清空聊天记录"):     st.session_state.chat_history = []     st.rerun()(msg["role"]):
        st.markdown(msg["content"])

# 2. 用户输入处理（避免重渲染冲突）
if prompt := st.chat_input("请输入天气的查询指令（例如：北京今天天气、上海未来3天天气）"):
    # 立即记录用户消息并渲染
    st.session_state.messages.append({"role": "user", "content": prompt})
    with import streamlit as st  # 初始化聊天历史（session_state 保存对话记录） if "chat_history" not in st.session_state:     st.session_state.chat_history = []  # 自定义聊天样式（通过 markdown 注入 CSS，美化气泡样式） def inject_chat_css():     st.markdown("""     <style>     /* 整体聊天容器 */     .chat-container {         margin: 10px 0;     }     /* 用户消息气泡 */     .user-message {         background-color: #262730;         color: white;         padding: 12px 18px;         border-radius: 18px;         margin: 8px 0;         max-width: 70%;         margin-left: auto;         text-align: right;     }     /* 助手（AI）消息气泡 */     .assistant-message {         background-color: #37384f;         color: white;         padding: 12px 18px;         border-radius: 18px;         margin: 8px 0;         max-width: 70%;         margin-right: auto;     }     /* 消息头像/标签 */     .message-role {         font-size: 12px;         opacity: 0.7;         margin-bottom: 4px;     }     /* 输入框样式（可选） */     .stTextInput>div>div>input {         border-radius: 20px;         padding: 10px 16px;     }     </style>     """, unsafe_allow_html=True)  # 渲染单条消息（核心函数：模拟 chat_message 效果） def render_message(role, content):     """     role: 消息角色（user/assistant）     content: 消息内容     """     # 定义角色名称和样式类     role_name = "你" if role == "user" else "AI助手"     style_class = "user-message" if role == "user" else "assistant-message"          # 渲染单条消息（容器+头像标签+气泡内容）     with st.container():         st.markdown(f"""         <div class="chat-container">             <div class="message-role">{role_name}</div>             <div class="{style_class}">{content}</div>         </div>         """, unsafe_allow_html=True)  # 1. 注入自定义样式 inject_chat_css()  # 2. 渲染聊天历史 st.subheader("聊天界面（模拟版）") chat_container = st.container()  # 聊天历史容器（固定位置，避免刷新闪烁） with chat_container:     for msg in st.session_state.chat_history:         render_message(msg["role"], msg["content"])  # 3. 输入框（模拟聊天输入） user_input = st.text_input("请输入消息：", placeholder="输入后按回车发送...", key="user_input")  # 4. 处理发送逻辑 if user_input and user_input.strip():     # 添加用户消息到历史     st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})     # 模拟AI回复（替换为你的实际业务逻辑，比如调用LLM）     ai_reply = f"已收到你的消息：{user_input.strip()}（这是模拟回复）"     # 添加AI消息到历史     st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})     # 清空输入框（关键：通过 rerun 刷新页面+清空输入）     st.session_state.user_input = ""     st.rerun()  # 刷新页面，实时显示新消息  # 可选：清空聊天记录按钮 if st.button("清空聊天记录"):     st.session_state.chat_history = []     st.rerun()("user"):
        st.markdown(prompt)
    
    # 处理查询逻辑（包裹在 try-except 中，避免中断渲染）
    try:
        with import streamlit as st  # 初始化聊天历史（session_state 保存对话记录） if "chat_history" not in st.session_state:     st.session_state.chat_history = []  # 自定义聊天样式（通过 markdown 注入 CSS，美化气泡样式） def inject_chat_css():     st.markdown("""     <style>     /* 整体聊天容器 */     .chat-container {         margin: 10px 0;     }     /* 用户消息气泡 */     .user-message {         background-color: #262730;         color: white;         padding: 12px 18px;         border-radius: 18px;         margin: 8px 0;         max-width: 70%;         margin-left: auto;         text-align: right;     }     /* 助手（AI）消息气泡 */     .assistant-message {         background-color: #37384f;         color: white;         padding: 12px 18px;         border-radius: 18px;         margin: 8px 0;         max-width: 70%;         margin-right: auto;     }     /* 消息头像/标签 */     .message-role {         font-size: 12px;         opacity: 0.7;         margin-bottom: 4px;     }     /* 输入框样式（可选） */     .stTextInput>div>div>input {         border-radius: 20px;         padding: 10px 16px;     }     </style>     """, unsafe_allow_html=True)  # 渲染单条消息（核心函数：模拟 chat_message 效果） def render_message(role, content):     """     role: 消息角色（user/assistant）     content: 消息内容     """     # 定义角色名称和样式类     role_name = "你" if role == "user" else "AI助手"     style_class = "user-message" if role == "user" else "assistant-message"          # 渲染单条消息（容器+头像标签+气泡内容）     with st.container():         st.markdown(f"""         <div class="chat-container">             <div class="message-role">{role_name}</div>             <div class="{style_class}">{content}</div>         </div>         """, unsafe_allow_html=True)  # 1. 注入自定义样式 inject_chat_css()  # 2. 渲染聊天历史 st.subheader("聊天界面（模拟版）") chat_container = st.container()  # 聊天历史容器（固定位置，避免刷新闪烁） with chat_container:     for msg in st.session_state.chat_history:         render_message(msg["role"], msg["content"])  # 3. 输入框（模拟聊天输入） user_input = st.text_input("请输入消息：", placeholder="输入后按回车发送...", key="user_input")  # 4. 处理发送逻辑 if user_input and user_input.strip():     # 添加用户消息到历史     st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})     # 模拟AI回复（替换为你的实际业务逻辑，比如调用LLM）     ai_reply = f"已收到你的消息：{user_input.strip()}（这是模拟回复）"     # 添加AI消息到历史     st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})     # 清空输入框（关键：通过 rerun 刷新页面+清空输入）     st.session_state.user_input = ""     st.rerun()  # 刷新页面，实时显示新消息  # 可选：清空聊天记录按钮 if st.button("清空聊天记录"):     st.session_state.chat_history = []     st.rerun()("assistant"):
            with st.spinner("正在查询天气..."):
                # 解析意图
                intent = parse_intent(prompt, LLM_API_KEY, LLM_TYPE)
                city = intent["city"]
                time_range = intent["time_range"]
                
                # 校验城市
                if city == "未指定":
                    response = "😥 我没识别到你要查询的城市哦，请告诉我具体城市名，比如「北京今天天气」"
                else:
                    # 获取天气并生成回答
                    weather_data = get_weather(city, time_range, QWEATHER_KEY)
                    response = generate_answer(weather_data)
                
                # 渲染回答
                st.markdown(response)
        # 记录助手消息
        st.session_state.messages.append({"role": "assistant", "content": response})
    except Exception as e:
        # 异常兜底，避免 DOM 崩溃
        error_msg = f"查询出错：{str(e)}"
        with import streamlit as st  # 初始化聊天历史（session_state 保存对话记录） if "chat_history" not in st.session_state:     st.session_state.chat_history = []  # 自定义聊天样式（通过 markdown 注入 CSS，美化气泡样式） def inject_chat_css():     st.markdown("""     <style>     /* 整体聊天容器 */     .chat-container {         margin: 10px 0;     }     /* 用户消息气泡 */     .user-message {         background-color: #262730;         color: white;         padding: 12px 18px;         border-radius: 18px;         margin: 8px 0;         max-width: 70%;         margin-left: auto;         text-align: right;     }     /* 助手（AI）消息气泡 */     .assistant-message {         background-color: #37384f;         color: white;         padding: 12px 18px;         border-radius: 18px;         margin: 8px 0;         max-width: 70%;         margin-right: auto;     }     /* 消息头像/标签 */     .message-role {         font-size: 12px;         opacity: 0.7;         margin-bottom: 4px;     }     /* 输入框样式（可选） */     .stTextInput>div>div>input {         border-radius: 20px;         padding: 10px 16px;     }     </style>     """, unsafe_allow_html=True)  # 渲染单条消息（核心函数：模拟 chat_message 效果） def render_message(role, content):     """     role: 消息角色（user/assistant）     content: 消息内容     """     # 定义角色名称和样式类     role_name = "你" if role == "user" else "AI助手"     style_class = "user-message" if role == "user" else "assistant-message"          # 渲染单条消息（容器+头像标签+气泡内容）     with st.container():         st.markdown(f"""         <div class="chat-container">             <div class="message-role">{role_name}</div>             <div class="{style_class}">{content}</div>         </div>         """, unsafe_allow_html=True)  # 1. 注入自定义样式 inject_chat_css()  # 2. 渲染聊天历史 st.subheader("聊天界面（模拟版）") chat_container = st.container()  # 聊天历史容器（固定位置，避免刷新闪烁） with chat_container:     for msg in st.session_state.chat_history:         render_message(msg["role"], msg["content"])  # 3. 输入框（模拟聊天输入） user_input = st.text_input("请输入消息：", placeholder="输入后按回车发送...", key="user_input")  # 4. 处理发送逻辑 if user_input and user_input.strip():     # 添加用户消息到历史     st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})     # 模拟AI回复（替换为你的实际业务逻辑，比如调用LLM）     ai_reply = f"已收到你的消息：{user_input.strip()}（这是模拟回复）"     # 添加AI消息到历史     st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})     # 清空输入框（关键：通过 rerun 刷新页面+清空输入）     st.session_state.user_input = ""     st.rerun()  # 刷新页面，实时显示新消息  # 可选：清空聊天记录按钮 if st.button("清空聊天记录"):     st.session_state.chat_history = []     st.rerun()("assistant"):
            st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
