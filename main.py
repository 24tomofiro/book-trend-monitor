import os
import yaml
import pandas as pd
from datetime import datetime
import pytz
from dotenv import load_dotenv
from src.crawler import BookCrawler
from src.visualizer import BookVisualizer

def get_time_slot(hour):
    """実行時刻から時間帯ラベルを返す"""
    if 5 <= hour < 11: return "morning"
    elif 11 <= hour < 17: return "afternoon"
    elif 17 <= hour < 23: return "evening"
    else: return "night"

def main():
    print(f"[{datetime.now().isoformat()}] Starting Book Trend Monitor...")

#     # 1. 環境変数の読み込み (.env または GitHub Secrets)
#     load_dotenv()
#     api_key = os.environ.get("GOOGLE_API_KEY")
#     cx = os.environ.get("GOOGLE_CX")

#     if not api_key or not cx:
#         print("❌ Error: GOOGLE_API_KEY or GOOGLE_CX is not set.")
#         return

#     # 2. 設定(books.yaml)の読み込み
#     config_path = "config/books.yaml"
#     if not os.path.exists(config_path):
#         print(f"❌ Error: {config_path} not found.")
#         return

#     with open(config_path, "r", encoding="utf-8") as f:
#         config = yaml.safe_load(f)
    
#     # 3. 各種モジュールの初期化
#     crawler = BookCrawler(api_key, cx)
#     jst = pytz.timezone('Asia/Tokyo')
#     now = datetime.now(jst)
#     time_slot = get_time_slot(now.hour)
    
#     results = []

#     # 4. 収集ループ
#     print(f"🔎 Scanning for {len(config['books'])} books (Slot: {time_slot})...")
#     for book in config['books']:
#         title = book['title']
#         # 除外ワードがある場合は、検索クエリに「-ワード」を追加
#         exclude_query = " ".join([f"-{w}" for w in book.get('exclude', [])])
#         keyword = "(" + " OR ".join(book['keywords']) + ") " + exclude_query
        
#         print(f"  - Processing: {title}")
        
#         # Web調査
#         web_count, web_links, web_sent = crawler.get_data(keyword)
#         # X調査 (site:x.com 限定)
#         x_count, x_links, x_sent = crawler.get_data(keyword, site="x.com")
        
#         results.append({
#             "date": now.strftime("%Y-%m-%d"),
#             "time_slot": time_slot,
#             "book_title": title,
#             "web_count": web_count,
#             "x_count": x_count,
#             "sentiment": round((web_sent + x_sent) / 2, 2),
#             "top_links": ",".join(x_links if x_links else web_links)
#         })

# # 5. CSV保存 (データ蓄積)
#     df_new = pd.DataFrame(results)
    csv_path = "data/processed/daily_stats.csv"
#     os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
#     # ファイルが存在し、かつ中身が空でないかチェック
#     if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
#         try:
#             df_old = pd.read_csv(csv_path)
#             df_final = pd.concat([df_old, df_new], ignore_index=True)
#             print(f"📖 Existing data loaded from {csv_path}")
#         except Exception as e:
#             print(f"⚠️ Could not read existing CSV ({e}). Creating new one.")
#             df_final = df_new
#     else:
#         # ファイルがない、または空の場合は新規作成
#         df_final = df_new
#         print(f"🆕 Creating new CSV at {csv_path}")
    
#     # 重複実行を防ぐため、同一日・同一時間帯・同一書籍のデータがあれば最新に更新
#     if not df_final.empty:
#         df_final.drop_duplicates(subset=['date', 'time_slot', 'book_title'], keep='last', inplace=True)
        
#     df_final.to_csv(csv_path, index=False, encoding="utf-8-sig")
#     print(f"✅ Successfully updated {csv_path}")

# 6. 可視化処理
    print("📊 Generating charts...")
    visualizer = BookVisualizer(csv_path)
    visualizer.generate_charts()

if __name__ == "__main__":
    main()