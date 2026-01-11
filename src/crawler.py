import requests
from bs4 import BeautifulSoup
import re
import time
import math

class BookCrawler:
    def __init__(self, api_key, cx):
        self.api_key = api_key
        self.cx = cx
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

    def _get_engagement_score(self, url):
        """メタタグからエンゲージメントを抽出（失敗しても0を返す）"""
        try:
            time.sleep(1) 
            res = requests.get(url, headers=self.headers, timeout=5)
            if res.status_code != 200: return 0
            
            soup = BeautifulSoup(res.text, 'html.parser')
            # 取得対象を拡大：og:description だけでなく、通常の description や title もチェック
            meta = soup.find("meta", property="og:description") or \
                   soup.find("meta", attrs={"name": "description"}) or \
                   soup.title
            
            text = ""
            if meta:
                text = meta.get("content", "") if meta.name == "meta" else meta.string
            
            # デバッグ用：何が読み取れているか確認（不要になったら消してください）
            # print(f"      [Debug] Meta Text: {text[:50]}...")

            nums = re.findall(r'(\d+[,.\d]*)\s*(?:Likes|いいね|Retweets|リツイート)', text or "")
            return sum(int(n.replace(',', '')) for n in nums)
        except:
            return 0

    def get_data(self, query, site=None, top_percentile=100):
        """広がりを取得し、深さ（スコア）が 0 でも上位リンクを保持する"""
        search_query = f"{query} site:{site}" if site else query
        api_url = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.cx}&q={search_query}"
        
        try:
            res = requests.get(api_url)
            data = res.json()
            reach_count = int(data.get("searchInformation", {}).get("totalResults", 0))
            items = data.get("items", [])
            
            all_scored_links = []
            for item in items:
                link = item["link"]
                score = self._get_engagement_score(link)
                all_scored_links.append({"link": link, "score": score})
            
            # スコア順にソート（スコアが同じならGoogleの検索順位を維持）
            all_scored_links.sort(key=lambda x: x["score"], reverse=True)
            
            # 上位xx%を抽出
            num_to_keep = max(1, math.ceil(len(all_scored_links) * (top_percentile / 100)))
            top_links = all_scored_links[:num_to_keep]
            
            # 【修正点】「if l['score'] > 0」を削除し、スコア0でも表示させる
            formatted_links = [f"{l['link']}|{l['score']}" for l in top_links]
            
            return reach_count, formatted_links
            
        except Exception as e:
            print(f"      ❌ Crawler Error: {e}")
            return 0, []