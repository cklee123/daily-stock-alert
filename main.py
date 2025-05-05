# main.py
# 股票自動分析 + Telegram 通知
# 你可以在 stocks 字典中加入要追蹤的股票代碼

import requests
import pandas as pd
from datetime import datetime, timedelta

# === TOKEN 設定 ===
API_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0wNS0wNCAwMToxMjoxMCIsInVzZXJfaWQiOiJjaGVuZ2thbmdsZWUiLCJpcCI6IjM5LjE0LjE3Ljg2In0.4Gc1eRyLwQrvRcDvlZRKCbNe-ZBrWhl3VrWgRmFU2_k'
BOT_TOKEN = '7223378639:AAHTpIAhz1TSlV_aKpITjlOq897aruvgwSc'
CHAT_ID = '7659097536'

# 股票清單
stocks = {
    '0050': '元大台灣50',
    '00965': '元大全球航太與防衛科技',
    '9908': '大台北',
    '2547': '日勝生'
}

def send_telegram(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, data=data)

def arrow(today, yesterday):
    if pd.isna(today) or pd.isna(yesterday):
        return "→"
    if today > yesterday:
        return "↑"
    elif today < yesterday:
        return "↓"
    else:
        return "→"

def bias_str(close, ma):
    if pd.isna(ma) or ma == 0:
        return "NA"
    bias = (close - ma) / ma * 100
    return f"{bias:+.2f}%"

def get_price_position(close, ma_dict):
    levels = list(ma_dict.items())
    levels.append(("價格", close))
    sorted_lv = sorted(levels, key=lambda x: -x[1])
    index = [label for label, _ in sorted_lv].index("價格")

    if index == 0:
        return f"高於所有均線（>{sorted_lv[1][0]}）"
    elif index == len(sorted_lv) - 1:
        return f"低於所有均線（<{sorted_lv[-2][0]}）"
    else:
        upper = sorted_lv[index - 1][0]
        lower = sorted_lv[index + 1][0]
        return f"介於 {upper} 和 {lower} 之間"

def get_ma_info(stock_id, name):
    url = 'https://api.finmindtrade.com/api/v4/data'
    params = {
        'dataset': 'TaiwanStockPrice',
        'data_id': stock_id,
        'start_date': (datetime.today() - timedelta(days=180)).strftime('%Y-%m-%d'),
        'token': API_TOKEN
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return f"{name}（{stock_id}）取得失敗，HTTP錯誤碼：{r.status_code}"

    data = r.json()
    if not data.get("data"):
        return f"{name}（{stock_id}）沒有資料"

    df = pd.DataFrame(data["data"])
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df = df.sort_index()

    # 技術指標計算
    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA10'] = df['close'].rolling(window=10).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA60'] = df['close'].rolling(window=60).mean()
    df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['DIF'] = df['EMA12'] - df['EMA26']
    df['MACD'] = df['DIF'].ewm(span=3, adjust=False).mean()
    df['OSC'] = df['DIF'] - df['MACD']

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    close = latest['close']

    # MA 字典與排序
    ma_dict = {
        "MA5": latest['MA5'],
        "MA10": latest['MA10'],
        "MA20": latest['MA20'],
        "MA60": latest['MA60']
    }

    ma_lines = []
    for label, val in sorted(ma_dict.items(), key=lambda x: -x[1]):
        prev_val = prev[label]
        ma_lines.append(f"  {label}：{val:.2f} {arrow(val, prev_val)}（乖離率：{bias_str(close, val)}）")

    # MACD 指標
    dif = f"{latest['DIF']:.2f} {arrow(latest['DIF'], prev['DIF'])}"
    macd = f"{latest['MACD']:.2f} {arrow(latest['MACD'], prev['MACD'])}"
    osc = f"{latest['OSC']:+.2f} {arrow(latest['OSC'], prev['OSC'])}"

    # 價格位置 + 均線排列
    level = get_price_position(close, ma_dict)
    sorted_order = [label for label, _ in sorted(ma_dict.items(), key=lambda x: -x[1])]
    if sorted_order == ["MA5", "MA10", "MA20", "MA60"]:
        trend = "多頭排列（MA5 > MA10 > MA20 > MA60）"
    elif sorted_order == ["MA60", "MA20", "MA10", "MA5"]:
        trend = "空頭排列（MA5 < MA10 < MA20 < MA60）"
    else:
        trend = "混合排列（" + " > ".join(sorted_order) + "）"

    msg = (
        f"{name}（{stock_id}）技術指標：\n"
        f"  收盤價：{close:.2f}\n"
        + "\n".join(ma_lines) + "\n"
        + f"  ➤ 價格位置：{level}\n"
        + f"  ➤ 均線排列：{trend}\n"
        + f"  ➤ MACD 指標：\n"
        + f"    DIF：{dif}\n"
        + f"    MACD：{macd}\n"
        + f"    OSC：{osc}"
    )
    return msg

# 執行主程式
messages = []
for stock_id, name in stocks.items():
    result = get_ma_info(stock_id, name)
    messages.append(result)

send_telegram('\n\n'.join(messages))

