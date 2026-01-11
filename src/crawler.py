import requests
from bs4 import BeautifulSoup
import re
import time
import math

class BookCrawler:
    def __init__(self, api_key, cx):
        self.api_key = api_key
        self.cx = cx
        # GitHub Actionsでの403エラーを回避するためのヘッダー
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

    def _get_engagement_score(self, url):
        """リンク先のメタタグからいいね・RT数を抽出する (深さ/Depthの計測)"""
        try:
            # サーバー負荷軽減のため1秒待機
            time.sleep(1) 
            res = requests.get(url, headers=self.headers, timeout=5)
            if res.status_code != 200:
                return 0
            
            soup = BeautifulSoup(res.text, 'html.parser')
            # 検索エンジン向けメタタグ(og:description等)から数値を抽出
            meta = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
            text = meta["content"] if meta else ""
            
            # 正規表現で数字と「Likes/いいね/Retweets/リツイート」の組み合わせを探す
            nums = re.findall(r'(\d+[,.\d]*)\s*(?:Likes|いいね|Retweets|リツイート)', text)
            # 全ての数値を合算してエンゲージメントスコアとする
            return sum(int(n.replace(',', '')) for n in nums)
        except Exception:
            # スクレイピング失敗時はスコア0として処理を継続
            return 0

    def get_data(self, query, site=None, top_percentile=100):
        """
        指定したクエリで調査を行い、広がり(Reach)と深さ(Depth)を返す。
        top_percentile: 上位何%のエンゲージメントリンクを保持するか
        """
        # site指定がある場合は site:x.com などを付与
        search_query = f"{query} site:{site}" if site else query
        api_url = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.cx}&q={search_query}"
        
        try:
            res = requests.get(api_url)
            data = res.json()
            
            # 広がり(Reach): Googleが認識している全件数
            reach_count = int(data.get("searchInformation", {}).get("totalResults", 0))
            items = data.get("items", [])
            
            # 深さ(Depth): 各リンクのエンゲージメントを計測
            all_scored_links = []
            for item in items:
                link = item["link"]
                score = self._get_engagement_score(link)
                all_scored_links.append({"link": link, "score": score})
            
            # スコアが高い順にソート
            all_scored_links.sort(key=lambda x: x["score"], reverse=True)
            
            # 相対的な抽出割合（上位xx%）に基づいてデータを絞り込む
            num_to_keep = max(1, math.ceil(len(all_scored_links) * (top_percentile / 100)))
            top_links = all_scored_links[:num_to_keep]
            
            # Visualizerが解釈できる "URL|Score" 形式のリストを作成
            formatted_links = [f"{l['link']}|{l['score']}" for l in top_links if l['score'] > 0]
            
            return reach_count, formatted_links
            
        except Exception as e:
            print(f"      ❌ Crawler Error for {query}: {e}")
            return 0, []