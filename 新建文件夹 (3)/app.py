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

# 侧边栏：API Key 配置（也可通过 Streamlit Secrets 配置）
with st.sidebar:
    st.title("🔧 配置项")
    QWEATHER_KEY = st.text_input("和风天气 API Key", type="password", value=os.getenv("QWEATHER_KEY", ""))
    LLM_API_KEY = st.text_input("大模型 API Key（OpenAI/智谱）", type="password", value=os.getenv("LLM_API_KEY", ""))
    LLM_TYPE = st.selectbox("大模型类型", ["openai", "zhipu"], index=0)

# 主页面标题
st.title("🌤️ 豆包天气智能体")
st.caption("支持自然语言查询全国城市天气 | 基于 Streamlit Cloud 部署")

# ===================== 核心工具函数 =====================
def parse_intent(user_input, llm_api_key, llm_type):
    """解析用户意图（城市+时间范围）"""
    prompt = f"""
    请严格按照JSON格式解析用户的天气查询指令，仅返回JSON，无其他内容：
    {{
        "city": "城市名（未指定则填'未指定'）",
        "time_range": "时间范围（今天/明天/未来3天/本周，默认今天）"
    }}
    用户输入：{user_input}
    """
    try:
        # OpenAI 调用
        if llm_type == "openai":
            import openai
            openai.api_key = llm_api_key
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            intent = json.loads(response.choices[0].message.content)
        # 智谱 GLM 调用
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
    """获取城市经纬度"""
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
    """获取天气数据"""
    loc = get_city_loc(city, qweather_key)
    if not loc:
        return {"error": f"未找到「{city}」的天气信息"}
    
    # 今日天气
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
    
    # 未来3天
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
    """生成自然语言回答"""
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

# ===================== 交互逻辑 =====================
# 初始化对话历史（Streamlit 会话状态）
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 显示历史对话
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])

# 用户输入框
user_input = st.chat_input("请输入天气查询指令（例如：北京今天天气、上海未来3天天气）")

if user_input:
    # 记录用户输入
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)
    
    # 核心流程：解析意图 → 获取天气 → 生成回答
    with st.spinner("正在查询天气..."):
        # 1. 解析意图
        intent = parse_intent(user_input, LLM_API_KEY, LLM_TYPE)
        city = intent["city"]
        time_range = intent["time_range"]
        
        # 2. 校验城市
        if city == "未指定":
            answer = "😥 我没识别到你要查询的城市哦，请告诉我具体城市名，比如「北京今天天气」"
        else:
            # 3. 获取天气数据
            weather_data = get_weather(city, time_range, QWEATHER_KEY)
            # 4. 生成回答
            answer = generate_answer(weather_data)
    
    # 显示并记录回答
    st.chat_message("assistant").markdown(answer)
    st.session_state.chat_history.append({"role": "assistant", "content": answer})