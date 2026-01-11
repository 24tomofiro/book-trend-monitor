import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

class BookVisualizer:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.output_dir = "plots"
        os.makedirs(self.output_dir, exist_ok=True)
        # ZenGakuTVのスタイルに合わせたフォントとアクセントカラー
        self.font_family = "Meiryo, Yu Gothic, sans-serif"
        self.accent_color = "#4a86e8" 

    def generate_charts(self):
        """個別レポートを生成：横軸を簡略化し、モバイル対応を完結させる"""
        if not os.path.exists(self.csv_path):
            return

        df = pd.read_csv(self.csv_path)
        if df.empty:
            return

        # 時間帯の表示を1文字に短縮
        slot_map = {
            'morning': '朝',
            'afternoon': '昼',
            'evening': '夜',
            'night': '晩'
        }

        books = df['book_title'].unique()

        for book in books:
            book_id = book.replace(' ', '_').replace('　', '_')
            plot_div_id = f"plot_{book_id}"
            display_div_id = f"links_{book_id}"
            
            book_df = df[df['book_title'] == book].copy()
            
            # --- 横軸表示の最適化（文字かぶり防止） ---
            # 2026-01-11 -> 01/11 に短縮し、時間帯を結合
            book_df['short_date'] = book_df['date'].str[5:].str.replace('-', '/')
            book_df['display_name'] = book_df['short_date'] + " " + book_df['time_slot'].map(slot_map)
            
            fig = make_subplots(
                rows=2, cols=1, 
                shared_xaxes=True,
                vertical_spacing=0.15,
                specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
                subplot_titles=(f"<b>{book}</b>: 言及数の推移", "<b>感情スコア</b>の推移"),
                row_heights=[0.6, 0.4]
            )

            # --- 1. 件数推移 (X投稿数: 左軸 / Web全体: 右軸) ---
            # X投稿数
            fig.add_trace(
                go.Scatter(x=book_df['display_name'], y=book_df['x_count'], 
                           name="X投稿数", mode='lines+markers', 
                           line=dict(color='#d62728', width=2.5),
                           marker=dict(size=7),
                           customdata=book_df['top_links'],
                           hovertemplate="日時: %{x}<br>X件数: %{y}件"),
                row=1, col=1, secondary_y=False
            )
            # Web全体
            fig.add_trace(
                go.Scatter(x=book_df['display_name'], y=book_df['web_count'], 
                           name="Web全体", mode='lines+markers', 
                           line=dict(color=self.accent_color, width=2.5),
                           marker=dict(size=7),
                           customdata=book_df['top_links'],
                           hovertemplate="日時: %{x}<br>Web件数: %{y}件"),
                row=1, col=1, secondary_y=True
            )

            # --- 2. 感情スコア ---
            fig.add_trace(
                go.Scatter(x=book_df['display_name'], y=book_df['sentiment'], 
                           name="感情スコア", mode='lines+markers', 
                           line=dict(color='#2ca02c', width=2.5),
                           fill='tozeroy', fillcolor='rgba(44, 160, 44, 0.05)'),
                row=2, col=1
            )

            # レイアウトと軸の枠線設定
            axis_config = dict(
                showline=True, linewidth=1, linecolor='black', mirror=True, 
                gridcolor='#eee', zeroline=False
            )

            fig.update_layout(
                height=700, paper_bgcolor='white', plot_bgcolor='white',
                font=dict(family=self.font_family, color="#333"),
                margin=dict(l=50, r=50, t=80, b=100),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            # X軸の設定（tickangle=0 で文字を重ならないように制御）
            fig.update_xaxes(row=1, col=1, **axis_config, tickangle=0, tickfont=dict(size=10))
            fig.update_xaxes(row=2, col=1, **axis_config, tickangle=0, tickfont=dict(size=10), rangeslider_visible=True)
            
            # Y軸の設定
            fig.update_yaxes(title_text="X投稿数", row=1, col=1, secondary_y=False, **axis_config)
            fig.update_yaxes(title_text="Web全体", row=1, col=1, secondary_y=True, showgrid=False, showline=True, linecolor='black')
            fig.update_yaxes(title_text="スコア", range=[0, 1.05], row=2, col=1, **axis_config)

            # --- JavaScript (クリック連動機能) ---
            js_template = """
            <script>
            (function() {
                var checkExist = setInterval(function() {
                    var myPlot = document.getElementById('{{PLOT_ID}}');
                    if (myPlot) {
                        clearInterval(checkExist);
                        myPlot.on('plotly_click', function(data) {
                            var pts = data.points[0];
                            var links = pts.customdata;
                            var dateStr = pts.x;
                            var display = document.getElementById('{{DISPLAY_ID}}');
                            if (links && links !== "なし") {
                                var linkList = links.split(',');
                                var html = '<h4 style="margin-top:0; color:#333;">📅 ' + dateStr + ' の注目リンク</h4>';
                                html += '<div style="display: flex; flex-wrap: wrap; gap: 10px;">';
                                linkList.forEach(function(url, i) {
                                    url = url.trim();
                                    html += '<a href="' + url + '" target="_blank" style="text-decoration:none; color:white; background:#4a86e8; padding:10px 18px; border-radius:8px; font-weight:bold; font-size:14px; box-shadow:0 2px 4px rgba(0,0,0,0.1);">🔗 リンク ' + (i+1) + '</a>';
                                });
                                html += '</div>';
                                display.innerHTML = html;
                                display.style.display = 'block';
                                display.scrollIntoView({behavior: "smooth", block: "nearest"});
                            }
                        });
                    }
                }, 100);
            })();
            </script>
            """
            script = js_template.replace('{{PLOT_ID}}', plot_div_id).replace('{{DISPLAY_ID}}', display_div_id)
            display_box = f'<div id="{display_div_id}" style="margin: 20px 15px; padding: 20px; border: 2px solid {self.accent_color}; border-radius: 12px; background-color: #f0f7ff; display: none; min-height: 80px;"></div>'

            plot_html = fig.to_html(include_plotlyjs='cdn', full_html=False, div_id=plot_div_id, config={'responsive': True})

            full_html = f"""
            <!DOCTYPE html>
            <html lang="ja">
            <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{book} Trend</title></head>
            <body style="background-color: #f8f9fa; padding: 10px; margin: 0;">
                <div style="max-width: 1000px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                    {plot_html}{display_box}
                </div>
                {script}
            </body>
            </html>
            """
            save_path = os.path.join(self.output_dir, f"{book}_interactive.html")
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(full_html)
            print(f"✅ レポート生成: {book}")

    def generate_portal(self):
        """ポータル画面：レスポンシブかつ洗練されたグリッドレイアウト"""
        if not os.path.exists(self.csv_path):
            return
        df = pd.read_csv(self.csv_path)
        if df.empty:
            return
        books = df['book_title'].unique()
        links_html = "".join([f'''
            <div class="card">
                <h3>{b}</h3>
                <p>最新トレンド & 感情分析</p>
                <a href="plots/{b}_interactive.html" class="btn">レポートを表示</a>
            </div>''' for b in books])

        portal_html = f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Book Trend Portal</title>
            <style>
                :root {{ --accent: {self.accent_color}; --bg: #f8f9fa; }}
                body {{ font-family: sans-serif; background: var(--bg); margin: 0; padding: 20px; }}
                h1 {{ text-align: center; color: var(--accent); margin: 20px 0 40px; font-weight: bold; }}
                .container {{ display: grid; gap: 20px; max-width: 1000px; margin: 0 auto; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
                .card {{ background: white; padding: 25px; border-radius: 18px; box-shadow: 0 6px 15px rgba(0,0,0,0.06); text-align: center; transition: 0.2s; }}
                .card:active {{ transform: scale(0.97); }}
                .btn {{ display: block; background: var(--accent); color: white; padding: 14px; text-decoration: none; border-radius: 10px; font-weight: bold; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <h1>📚 書籍トレンド監視ポータル</h1>
            <div class="container">{links_html}</div>
            <footer style="margin-top:50px; color:#aaa; font-size:0.8rem; text-align:center;">
                最終更新: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
            </footer>
        </body>
        </html>
        """
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(portal_html)
        print("🏠 ポータル作成完了 (index.html)")