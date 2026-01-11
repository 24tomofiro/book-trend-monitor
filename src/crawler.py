import os
import requests
from datetime import datetime

class BookCrawler:
    # 外部からキーを受け取るように変更
    def __init__(self, api_key, cx):
        self.api_key = api_key
        self.cx = cx
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def get_data(self, keyword, site=None):
        query = f"{keyword} site:{site}" if site else keyword
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "dateRestrict": "d1" # 過去24時間
        }
        
        try:
            res = requests.get(self.base_url, params=params).json()
            count = int(res.get("searchInformation", {}).get("totalResults", 0))
            items = res.get("items", [])
            
            # 上位3つのリンクと簡易ポジネガ判定
            top_links = [item.get("link") for item in items[:3]]
            sentiment_score = self._quick_sentiment_analysis(items)
            
            return count, top_links, sentiment_score
        except Exception as e:
            print(f"Error fetching data for {keyword}: {e}")
            return 0, [], 0.5

    def _quick_sentiment_analysis(self, items):
        # 簡易的なキーワードマッチングによるポジネガ判定
        pos_words = ["面白い", "最高", "勉強になった", "おすすめ", "救われた"]
        neg_words = ["微妙", "合わない", "難しい", "ひどい", "つまらない"]
        
        score = 0.5 # 中立
        text = "".join([item.get("snippet", "") for item in items]).lower()
        
        pos_count = sum(1 for w in pos_words if w in text)
        neg_count = sum(1 for w in neg_words if w in text)
        
        if pos_count + neg_count > 0:
            score = pos_count / (pos_count + neg_count)
        return round(score, 2)