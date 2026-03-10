# 微信文章生成器 (weixin_article)

每天自动生成一篇模仿诺贝尔获奖者风格的文章，发布到微信公众号草稿箱。

## 功能

- 🎲 随机选择诺贝尔文学奖/经济学奖得主
- ✍️ 模仿其写作风格生成文章（散文/故事/评论）
- 🎨 自动生成配图（MiniMax API）
- 📝 发布到微信公众号草稿箱
- ⏰ 每天 8:00 自动运行（crontab）

## 配置

1. 复制配置模板：
```bash
cp config.example.py config.py
```

2. 填写 API 密钥：
- `WECHAT_APPID` - 微信公众号 AppID
- `WECHAT_SECRET` - 微信公众号 AppSecret
- `MINIMAX_API_KEY` - MiniMax 生图 API Key
- `GLM_API_KEY` - 智谱 GLM API Key

3. 配置生图 API Key：
```bash
echo "your-minimax-api-key" > api_key.txt
```

## 运行

```bash
# 手动运行
python3 generator.py

# 设置定时任务（每天 8:00）
(crontab -l 2>/dev/null; echo "0 8 * * * cd /path/to/weixin_article && /usr/bin/python3 generator.py >> /path/to/logs/weixin_article.log 2>&1") | crontab -
```

## 文件结构

```
weixin_article/
├── generator.py      # 主程序
├── laureates.py      # 诺贝尔获奖者数据库（68位）
├── config.py         # 配置文件（需自行创建）
├── config.example.py # 配置模板
├── image_generator.py # 生图工具
├── api_key.txt       # MiniMax API Key
├── output/           # 输出目录
│   ├── cover_*.png   # 生成的配图
│   └── record_*.json # 每日记录
└── README.md
```

## 获奖者数据

- 文学奖：44 位
- 经济学奖：24 位
- 总计：68 位

每位获奖者包含：姓名、年份、类别、国籍、风格特点

## 许可

MIT
