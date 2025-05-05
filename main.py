# main.py
# 股票自動分析 + Telegram 通知
# 你可以在 stocks 字典中加入要追蹤的股票代碼

import requests
import pandas as pd
from datetime import datetime, timedelta
import os

API_TOKEN = os.environ.get('API_TOKEN')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

stocks = {
    '0050': '元大台灣50',
    '00965': '元大全球航太與防衛科技',
    '1810': '和成',
    '2547': '日勝生'
}

# 你可以在這裡加入程式邏輯
print("自動化程式已啟動...")
