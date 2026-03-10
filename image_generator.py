import requests
import os
import sys
import json
import base64
from datetime import datetime
import re


def get_api_key():
    """获取 API Key，优先从文件读取，其次从环境变量"""
    # 先尝试从文件读取
    api_key_file = os.path.join(os.path.dirname(__file__), "api_key.txt")
    if os.path.exists(api_key_file):
        with open(api_key_file, "r", encoding="utf-8") as f:
            api_key = f.read().strip()
            if api_key:
                return api_key

    # 再尝试从环境变量读取
    return os.environ.get("MINIMAX_API_KEY")


def sanitize_filename(name):
    """清理文件名，移除非法字符"""
    # 替换非法字符为下划线
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # 限制长度
    if len(name) > 50:
        name = name[:50]
    return name


def generate_image(prompt, model="image-01", aspect_ratio="1:1", n=1, 
                   response_format="base64"):
    """生成图片并保存为文件"""

    url = "https://api.minimaxi.com/v1/image_generation"
    api_key = get_api_key()

    if not api_key:
        print("错误: 请在 api_key.txt 文件中设置 API Key，或设置环境变量 MINIMAX_API_KEY")
        return None

    print(f"✅ API Key 已加载 (长度: {len(api_key)})")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "response_format": response_format,
        "n": n,
        "prompt_optimizer": True
    }

    print(f"\n=== 正在生成图片 ===")
    print(f"模型: {model}")
    print(f"提示词: {prompt}")
    print(f"宽高比: {aspect_ratio}")
    print(f"数量: {n}")

    response = requests.post(url, headers=headers, json=payload)
    result = response.json()

    print(f"\n=== 响应状态码 ===")
    print(response.status_code)

    if response.status_code != 200:
        print(f"\n=== 错误内容 ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return None

    # 创建 output 目录
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 生成文件名（使用提示词和时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prompt_short = sanitize_filename(prompt[:30])
    base_filename = f"{prompt_short}_{timestamp}"

    # 解析返回的 base64 数据
    if response_format == "base64":
        image_base64_list = result.get("data", {}).get("image_base64", [])

        if not image_base64_list:
            print("错误: 未获取到图片数据")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return None

        print(f"\n成功生成 {len(image_base64_list)} 张图片")

        saved_files = []
        for i, img_b64 in enumerate(image_base64_list):
            # 生成文件名
            if len(image_base64_list) > 1:
                filename = f"{base_filename}_{i+1}.png"
            else:
                filename = f"{base_filename}.png"

            filepath = os.path.join(output_dir, filename)

            # 解码并保存图片
            try:
                img_data = base64.b64decode(img_b64)
                with open(filepath, "wb") as f:
                    f.write(img_data)
                print(f"✅ 图片已保存: output/{filename} ({len(img_data)/1024:.1f} KB)")
                saved_files.append(filepath)
            except Exception as e:
                print(f"❌ 保存图片失败: {e}")

        return saved_files
    else:
        # URL 格式
        image_urls = result.get("data", {}).get("image_urls", [])
        print(f"\n=== 图片链接 ===")
        for url in image_urls:
            print(url)
        return image_urls


if __name__ == "__main__":
    # 默认提示词
    default_prompt = "A beautiful Chinese New Year celebration scene, red lanterns, fireworks, family reunion dinner, festive atmosphere, photorealistic style"

    # 可以通过命令行参数指定提示词
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = default_prompt

    # 生成图片
    generate_image(prompt=prompt, n=1)
