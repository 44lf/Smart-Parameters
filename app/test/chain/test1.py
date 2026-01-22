import os
from dotenv import find_dotenv, load_dotenv

print("CWD:", os.getcwd())

# 1) 看 python-dotenv 最终会找到哪个 .env
env_path = find_dotenv(usecwd=True)
print("find_dotenv:", env_path or "<NOT FOUND>")

# 2) 先不加载，观察进程启动时就有没有变量（关键）
print("KEY exists before load_dotenv:", "DEEPSEEK_API_KEY" in os.environ)
print("KEY last4 before:", os.getenv("DEEPSEEK_API_KEY", "")[-4:])

# 3) 再尝试加载（分别测试 override=False/True）
loaded_no_override = load_dotenv(env_path, override=False) if env_path else False
print("load_dotenv override=False:", loaded_no_override)
print("KEY last4 after override=False:", os.getenv("DEEPSEEK_API_KEY", "")[-4:])

loaded_override = load_dotenv(env_path, override=True) if env_path else False
print("load_dotenv override=True:", loaded_override)
print("KEY last4 after override=True:", os.getenv("DEEPSEEK_API_KEY", "")[-4:])
