from dotenv import load_dotenv
import os
import requests

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("BASE_URL")

print("=== 环境变量检查 ===")
print(f"API Key: {api_key[:8]}...{api_key[-4:] if api_key else 'None'}")
print(f"BASE_URL: {base_url}")
print()

# 测试 API
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 10
}

try:
    print("=== 测试 API 连接 ===")
    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=data,
        timeout=10
    )

    if response.status_code == 200:
        print("✓ API Key 有效!")
        print("响应:", response.json()['choices'][0]['message']['content'])
    else:
        print("✗ 认证失败")
        print(f"状态码: {response.status_code}")
        print(f"错误: {response.text}")

except Exception as e:
    print(f"✗ 请求失败: {e}")