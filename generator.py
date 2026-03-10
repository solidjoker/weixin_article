#!/usr/bin/env python3
"""
诺贝尔作家文章生成器
每天随机选一位诺贝尔文学奖/经济学奖得主，模仿其风格生成文章，发布到微信公众号草稿箱
"""

import os
import sys
import json
import random
import base64
import requests
import re
from datetime import datetime
from typing import Optional, Tuple

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import *
from laureates import LAUREATES


def ensure_output_dir():
    """确保输出目录存在"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


def select_random_laureate() -> dict:
    """随机选择一位诺贝尔获奖者"""
    return random.choice(LAUREATES)


def generate_article(laureate: dict = None, article_type: str = None, theme: str = None) -> Tuple[str, str]:
    """
    使用 GLM 生成文章
    返回: (标题, 正文)
    """
    if not article_type:
        article_type = random.choice(ARTICLE_TYPES)
    
    # 判断是否是融合风格模式
    is_fusion_mode = theme and "【风格融合要求】" in theme
    
    if is_fusion_mode:
        # 融合风格模式：主题中已包含风格要求
        style_prompt = f"""
你是一位文学大师，擅长融合多种诺贝尔获奖者的写作风格。

{theme}

【任务要求】
1. 写一篇{article_type}，字数在800-1000字
2. 必须体现融合后的独特风格特征
3. 语言要有质感，避免流水账
4. 标题要有文学性，不要用"论xxx"这种学术式标题
5. 深度思考，不要流于表面

【输出格式】
第一行是标题（不要序号、不要书名号）
空一行
然后是正文

现在开始创作：
"""
    else:
        # 单一作家模式
        if not laureate:
            laureate = select_random_laureate()
        
        # 主题部分
        theme_section = f"""
【指定主题】
{theme}

请围绕这个主题创作，结合作家的风格特点来展开。
""" if theme else """
【主题自选】
可以是：记忆、身份、日常、自然、时间、人性等
"""
        
        # 构建风格提示
        style_prompt = f"""
你是一位模仿大师，现在要模仿诺贝尔{laureate['category']}得主 {laureate['name']} 的写作风格。

【作家信息】
- 姓名：{laureate['name']}
- 国籍：{laureate['country']}
- 获奖年份：{laureate['year']}年
- 风格特点：{laureate['style']}

{theme_section}
【任务要求】
1. 写一篇{article_type}，字数在800-1000字
2. 必须体现该作家的核心风格特征
3. 语言要有质感，避免流水账
4. 标题要有文学性，不要用"论xxx"这种学术式标题

【输出格式】
第一行是标题（不要序号、不要书名号）
空一行
然后是正文

现在开始创作：
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GLM_API_KEY}"
    }
    
    payload = {
        "model": GLM_MODEL,
        "messages": [
            {"role": "user", "content": style_prompt}
        ],
        "temperature": 0.9,
        "max_tokens": 2000
    }
    
    if is_fusion_mode:
        print(f"📝 正在生成文章（融合风格，{article_type}）...")
    else:
        print(f"📝 正在生成文章（模仿 {laureate['name']}，{article_type}）...")
    
    response = requests.post(GLM_API_URL, headers=headers, json=payload, timeout=60)
    
    if response.status_code != 200:
        raise Exception(f"GLM API 调用失败: {response.status_code} - {response.text}")
    
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    
    # 解析标题和正文
    lines = content.strip().split("\n")
    title = lines[0].strip()
    # 移除标题中可能的序号
    title = re.sub(r'^[一二三四五六七八九十\d\.、\s]+', '', title)
    body = "\n".join(lines[2:]).strip()
    
    print(f"✅ 文章生成完成：{title}")
    return title, body


def generate_image_for_article(title: str, body: str, laureate: dict) -> str:
    """
    使用 MiniMax 生成配图
    返回: 图片文件路径
    """
    ensure_output_dir()
    
    # 构建图片提示词（英文，更具描述性）
    image_prompt = f"""
Create an artistic illustration for a literary article.
Style: {laureate['style']}, artistic, evocative, minimalist
Theme: Based on the title "{title}"
Mood: contemplative, literary, elegant
Medium: digital art, soft colors, abstract or semi-abstract
Quality: high quality, suitable for WeChat article header
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MINIMAX_API_KEY}"
    }
    
    payload = {
        "model": "image-01",
        "prompt": image_prompt,
        "aspect_ratio": "16:9",  # 横版，适合文章头图
        "response_format": "base64",
        "n": 1,
        "prompt_optimizer": True
    }
    
    print(f"🎨 正在生成配图...")
    
    response = requests.post(MINIMAX_API_URL, headers=headers, json=payload, timeout=120)
    
    if response.status_code != 200:
        raise Exception(f"MiniMax API 调用失败: {response.status_code} - {response.text}")
    
    result = response.json()
    image_base64 = result.get("data", {}).get("image_base64", [])
    
    if not image_base64:
        raise Exception("未能获取图片数据")
    
    # 保存图片
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cover_{timestamp}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    img_data = base64.b64decode(image_base64[0])
    with open(filepath, "wb") as f:
        f.write(img_data)
    
    print(f"✅ 配图生成完成: {filename}")
    return filepath


def get_wechat_access_token() -> str:
    """获取微信 access_token"""
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={WECHAT_APPID}&secret={WECHAT_SECRET}"
    
    response = requests.get(url, timeout=30)
    result = response.json()
    
    if "access_token" not in result:
        raise Exception(f"获取 access_token 失败: {result}")
    
    print(f"✅ 获取 access_token 成功")
    return result["access_token"]


def upload_image_to_wechat(access_token: str, image_path: str) -> str:
    """
    上传图片到微信，获取 media_id
    返回: media_id
    """
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    
    with open(image_path, "rb") as f:
        files = {"media": (os.path.basename(image_path), f, "image/png")}
        response = requests.post(url, files=files, timeout=60)
    
    result = response.json()
    
    if "media_id" not in result:
        raise Exception(f"上传图片失败: {result}")
    
    print(f"✅ 图片上传成功，media_id: {result['media_id'][:20]}...")
    return result["media_id"]


def create_draft(access_token: str, title: str, content: str, thumb_media_id: str) -> str:
    """
    创建微信草稿
    返回: media_id（草稿ID）
    """
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    
    # 构建文章 HTML 内容
    html_content = f"""
<section style="padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.8; color: #333;">
    <div style="text-align: center; margin-bottom: 30px;">
        <img src="{thumb_media_id}" style="max-width: 100%; border-radius: 8px;" />
    </div>
    <div style="font-size: 16px; text-align: justify;">
        {content.replace(chr(10), '</p><p>')}
    </div>
    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #999; text-align: center;">
        本文由 AI 模仿诺贝尔获奖者风格创作
    </div>
</section>
"""
    
    # 简化版内容（微信要求）
    simple_content = f"<p>{content.replace(chr(10), '</p><p>')}</p>"
    
    articles = {
        "articles": [
            {
                "title": title,
                "author": "AI写作",
                "content": simple_content,
                "thumb_media_id": thumb_media_id,
                "need_open_comment": 1,
                "only_fans_can_comment": 0
            }
        ]
    }
    
    # 使用 ensure_ascii=False 保持中文字符不被转义
    headers = {"Content-Type": "application/json; charset=utf-8"}
    response = requests.post(url, data=json.dumps(articles, ensure_ascii=False).encode('utf-8'), headers=headers, timeout=30)
    result = response.json()
    
    if "media_id" not in result:
        raise Exception(f"创建草稿失败: {result}")
    
    print(f"✅ 草稿创建成功，media_id: {result['media_id']}")
    return result["media_id"]


def main():
    """主流程"""
    print("=" * 50)
    print(f"📚 诺贝尔作家文章生成器 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        # 检查是否有指定主题文件
        theme_file = os.path.join(PROJECT_DIR, "theme.txt")
        theme = None
        if os.path.exists(theme_file):
            with open(theme_file, "r", encoding="utf-8") as f:
                theme = f.read().strip()
            # 提取主题摘要（第一行）
            theme_summary = theme.split('\n')[0]
            print(f"\n📌 指定主题: {theme_summary}")
            # 使用后删除，避免重复
            os.remove(theme_file)
        
        # 判断是否是融合风格模式
        is_fusion_mode = theme and "【风格融合要求】" in theme
        
        if is_fusion_mode:
            print(f"\n🎭 融合风格模式")
            laureate = None
        else:
            # 1. 随机选择获奖者
            laureate = select_random_laureate()
            print(f"\n🎲 今日获奖者: {laureate['name']} ({laureate['year']}年 {laureate['category']})")
            print(f"   风格: {laureate['style']}")
        
        # 2. 生成文章
        title, body = generate_article(laureate, theme=theme)
        print(f"\n📄 文章标题: {title}")
        print(f"   字数: {len(body)} 字")
        
        # 3. 生成配图
        style_for_image = laureate['style'] if laureate else "融合多种文学风格，存在主义，记忆与时间，社会学视角"
        image_path = generate_image_for_article(title, body, {"style": style_for_image})
        
        # 4. 获取微信 access_token
        access_token = get_wechat_access_token()
        
        # 5. 上传图片
        thumb_media_id = upload_image_to_wechat(access_token, image_path)
        
        # 6. 创建草稿
        draft_media_id = create_draft(access_token, title, body, thumb_media_id)
        
        print("\n" + "=" * 50)
        print("🎉 任务完成！草稿已保存到微信公众号后台")
        print(f"   草稿ID: {draft_media_id}")
        print("=" * 50)
        
        # 保存今日记录
        record = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "mode": "fusion" if is_fusion_mode else "single",
            "laureate": laureate if laureate else "融合风格：加缪+石黑一雄+阿马蒂亚·森+多丽丝·莱辛+莫言",
            "title": title,
            "word_count": len(body),
            "image_path": image_path,
            "draft_media_id": draft_media_id,
            "status": "success"
        }
        
        record_file = os.path.join(OUTPUT_DIR, f"record_{datetime.now().strftime('%Y%m%d')}.json")
        with open(record_file, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
