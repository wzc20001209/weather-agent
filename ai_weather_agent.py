from openai import OpenAI
import requests

# ===================== 配置 =====================
# 你在百炼拿到的 sk- 开头 Key
DASHSCOPE_API_KEY = "sk-4efbf7b966a44fb5855db305f2c485b1"
# 高德天气API Key（之前申请的）
GAODE_KEY = "291d51bd2283a2f57e18ec482c6f2a3d"
# ==================================================

# 百炼新版客户端配置
client = OpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def get_weather(city):
    """调用高德API获取真实天气"""
    if not city:
        return None
    try:
        # 获取城市编码
        city_url = f"https://restapi.amap.com/v3/geocode/geo?address={city}&key={GAODE_KEY}&output=JSON"
        adcode = requests.get(city_url).json()["geocodes"][0]["adcode"]
        
        # 获取天气
        weather_url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={GAODE_KEY}&extensions=base"
        data = requests.get(weather_url).json()["lives"][0]
        return f"{data['city']}当前：{data['weather']}，气温{data['temperature']}℃，湿度{data['humidity']}%"
    except:
        return None

def ai_weather_agent(query):
    """AI智能体：自动判断+查天气+回答"""
    # 让AI判断是否查天气，并提取城市
    prompt = f'''
用户问题：{query}
请判断：
1. 是否需要查询天气？ 只回复 是/否
2. 如果需要，城市是什么？

输出格式：
需要天气查询：是/否
城市：xxx
'''
    
    # 调用通义千问
    response = client.chat.completions.create(
        model="qwen-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    result = response.choices[0].message.content
    
    # 解析结果
    if "需要天气查询：是" in result:
        city = result.split("城市：")[-1].strip()
        weather = get_weather(city)
        if weather:
            return f"🌤️ {weather}"
        else:
            return "找不到这个城市的天气哦~"
    else:
        # 普通闲聊直接AI回答
        reply = client.chat.completions.create(
            model="qwen-turbo",
            messages=[{"role": "user", "content": query}]
        )
        return reply.choices[0].message.content

# 启动智能体
if __name__ == "__main__":
    # 测试模式
    print("=== 测试模式 ===")
    test_queries = [
        "南昌天气如何",
        "北京今天天气",
        "你好，今天过得怎么样？"
    ]
    
    for query in test_queries:
        print(f"\n测试：{query}")
        result = ai_weather_agent(query)
        print(f"智能体：{result}")
    
    # 交互式模式
    print("\n=== 交互式模式 ===")
    print("🌤️ AI天气智能体已启动（输入 exit 退出）")
    while True:
        user_input = input("你：")
        if user_input.lower() == "exit":
            print("👋 再见！")
            break
        print("智能体：", ai_weather_agent(user_input))
