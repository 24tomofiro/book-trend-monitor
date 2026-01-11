import os
import yaml
import pandas as pd
from datetime import datetime
import pytz
from dotenv import load_dotenv

# 自作モジュールのインポート
from src.crawler import BookCrawler
from src.visualizer import BookVisualizer

def get_time_slot(hour):
    """実行時刻（24時間制）から時間帯ラベルを返す"""
    if 5 <= hour < 11:
        return "morning"
    elif 11 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 23:
        return "evening"
    else:
        return "night"

def main():
    # 1. 初期設定と環境変数の読み込み
    # GitHub Actions等のサーバー環境でも日本時間を正確に維持
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.now(jst)
    print(f"[{now.isoformat()}] Starting Book Trend Monitor...")

    load_dotenv()
    api_key = os.environ.get("GOOGLE_API_KEY")
    cx = os.environ.get("GOOGLE_CX")
    
    if not api_key or not cx:
        print("❌ Error: GOOGLE_API_KEY or GOOGLE_CX is not set in environment variables.")
        return

    # 2. 設定(config/books.yaml)の読み込み
    config_path = "config/books.yaml"
    if not os.path.exists(config_path):
        print(f"❌ Error: {config_path} not found.")
        return
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    if not config or 'books' not in config:
        print("❌ Error: Invalid config file format.")
        return

    # 3. モジュールの初期化
    crawler = BookCrawler(api_key, cx)
    time_slot = get_time_slot(now.hour)
    results = []

    # 4. データ収集ループ (Reach/広がり と Depth/深さ の両立)
    print(f"🔎 Scanning for {len(config['books'])} books (Slot: {time_slot})...")
    
    for book in config['books']:
        title = book['title']
        # 相対的な抽出割合（上位xx%）を取得。設定がない場合は100%（全件）を表示
        percentile = book.get('top_percentile', 100)
        
        # 検索クエリの構築
        exclude_query = " ".join([f"-{w}" for w in book.get('exclude', [])])
        keyword = "(" + " OR ".join(book['keywords']) + ") " + exclude_query
        
        print(f"  - Processing: {title} (Target: Top {percentile}%)")
        
        # Web調査 (広がり/Reach の件数のみ利用)
        web_count, _ = crawler.get_data(keyword)
        
        # X調査 (深さ/Depth を含めた URL|スコア のリストを取得)
        x_count, x_links_with_scores = crawler.get_data(
            keyword, 
            site="x.com", 
            top_percentile=percentile
        )
        
        results.append({
            "date": now.strftime("%Y-%m-%d"),
            "time_slot": time_slot,
            "book_title": title,
            "web_count": web_count,
            "x_count": x_count,
            "sentiment": 0.5, # 必要に応じて将来的に感情分析を追加可能
            # "url|score" 形式で保存し、Visualizer側で数値を分離表示する
            "top_links": ",".join(x_links_with_scores) if x_links_with_scores else "なし"
        })

    # 5. CSV保存 (データの永続化と重複排除)
    df_new = pd.DataFrame(results)
    csv_path = "data/processed/daily_stats.csv"
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        try:
            df_old = pd.read_csv(csv_path)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
            print(f"📖 Existing data loaded from {csv_path}")
        except Exception as e:
            print(f"⚠️ Could not read existing CSV ({e}). Creating new file.")
            df_final = df_new
    else:
        df_final = df_new
        print(f"🆕 Creating new CSV at {csv_path}")
    
    # 同一の日付・時間帯・書籍があれば最新の実行結果を保持
    if not df_final.empty:
        df_final.drop_duplicates(subset=['date', 'time_slot', 'book_title'], keep='last', inplace=True)
        # 時系列順にソートして保存
        df_final.sort_values(by=['date', 'time_slot'], ascending=True, inplace=True)
      
    df_final.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"✅ Successfully updated {csv_path}")

    # 6. 可視化処理 (ZenGakuTVブランドのデザイン適用)
    print("📊 Generating charts and portal...")
    visualizer = BookVisualizer(csv_path)
    
    # 各書籍の個別レポートとポータル画面を生成
    visualizer.generate_charts()
    visualizer.generate_portal()
    
    print(f"✨ All tasks completed at {datetime.now(jst).strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()