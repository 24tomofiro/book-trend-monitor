import os
import requests

# テスト時は環境変数または直接入力
os.environ["GOOGLE_API_KEY"] = "AIzaSyA4DS07SYxlf0np8mQlcuLMyD9Wlpa9330"
os.environ["GOOGLE_CX"] = "a632b64dae0af4265"

def check_popularity(keyword, site=None):
    api_key = os.environ.get("GOOGLE_API_KEY")
    cx = os.environ.get("GOOGLE_CX")
    
    query = f"{keyword} site:{site}" if site else keyword
    url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={query}&dateRestrict=d1"
    
    res = requests.get(url).json()
    count = res.get("searchInformation", {}).get("totalResults", "0")
    return count

# 実行テスト
keyword = "嫌われる勇気"
print(f"Web全体: {check_popularity(keyword)}件")
print(f"X(Twitter): {check_popularity(keyword, 'x.com')}件")