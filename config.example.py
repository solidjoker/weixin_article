# 微信公众号配置
WECHAT_APPID = "your-wechat-appid"
WECHAT_SECRET = "your-wechat-secret"

# MiniMax 生图配置
MINIMAX_API_KEY = "your-minimax-api-key"
MINIMAX_API_URL = "https://api.minimaxi.com/v1/image_generation"

# GLM AI 配置（用于生成文章）
GLM_API_KEY = "your-glm-api-key"
GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
GLM_MODEL = "glm-4-flash"

# 文章配置
ARTICLE_WORD_COUNT = (800, 1000)  # 字数范围
ARTICLE_TYPES = ["散文", "故事", "评论"]

# 项目路径
import os
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")
