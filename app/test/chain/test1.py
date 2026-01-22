import os
import glob

# 查找所有可能包含 API key 的文件
patterns = [
    '**/.env*',
    '**/config.py',
    '**/settings.py',
    '**/*.ini',
    '**/*.yaml',
    '**/*.yml',
    '**/*.json'
]

print("=== 搜索包含 '7cd7' 的文件 ===\n")

search_dir = r"D:\project_new\fastApiProject1"
found_files = []

for pattern in patterns:
    for filepath in glob.glob(os.path.join(search_dir, pattern), recursive=True):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if '7cd7' in content or 'sk-' in content:
                    found_files.append(filepath)
                    print(f"✓ 找到: {filepath}")
                    # 显示匹配行
                    for i, line in enumerate(content.split('\n'), 1):
                        if '7cd7' in line or ('sk-' in line and 'API' in line.upper()):
                            print(f"  第{i}行: {line.strip()}")
                    print()
        except:
            pass

if not found_files:
    print("未找到包含旧 API key 的文件")
else:
    print(f"\n总共找到 {len(found_files)} 个文件")