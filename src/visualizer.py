import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

class BookVisualizer:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.output_dir = "plots"
        os.makedirs(self.output_dir, exist_ok=True)
        self.font_family = "Meiryo, Yu Gothic, sans-serif"

    def generate_charts(self):
        """各書籍の個別インタラクティブレポートを生成する"""
        if not os.path.exists(self.csv_path):
            return

        df = pd.read_csv(self.csv_path)
        if df.empty:
            return

        books = df['book_title'].unique()

        for book in books:
            book_id = book.replace(' ', '_').replace('　', '_')
            plot_div_id = f"plot_{book_id}"
            display_div_id = f"links_{book_id}"
            
            book_df = df[df['book_title'] == book].copy()
            book_df['datetime'] = book_df['date'] + " " + book_df['time_slot']
            
            fig = make_subplots(
                rows=2, cols=1, 
                shared_xaxes=True,
                vertical_spacing=0.15,
                specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
                subplot_titles=(f"<b>{book}</b>: 言及数の推移（点をクリックすると下にリンク表示）", "<b>感情スコア</b>の推移"),
                row_heights=[0.6, 0.4]
            )

            # 1. 件数推移
            fig.add_trace(
                go.Scatter(x=book_df['datetime'], y=book_df['x_count'], 
                           name="X投稿数", mode='lines+markers', 
                           line=dict(color='#d62728', width=3),
                           customdata=book_df['top_links'],
                           hovertemplate="日時: %{x}<br>X件数: %{y}件"),
                row=1, col=1, secondary_y=False
            )
            fig.add_trace(
                go.Scatter(x=book_df['datetime'], y=book_df['web_count'], 
                           name="Web全体", mode='lines+markers', 
                           line=dict(color='#1f77b4', width=3),
                           customdata=book_df['top_links'],
                           hovertemplate="日時: %{x}<br>Web件数: %{y}件"),
                row=1, col=1, secondary_y=True
            )

            # 2. 感情スコア
            fig.add_trace(
                go.Scatter(x=book_df['datetime'], y=book_df['sentiment'], 
                           name="感情スコア", mode='lines+markers', 
                           line=dict(color='#2ca02c', width=3),
                           fill='tozeroy', fillcolor='rgba(44, 160, 44, 0.1)'),
                row=2, col=1
            )

            fig.update_layout(
                height=800, paper_bgcolor='white', plot_bgcolor='white',
                font=dict(family=self.font_family),
                margin=dict(l=80, r=80, t=80, b=150),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            axis_config = dict(showline=True, linewidth=1, linecolor='black', mirror=True, gridcolor='#eee')
            fig.update_xaxes(row=1, col=1, **axis_config)
            fig.update_yaxes(title_text="X投稿数", row=1, col=1, secondary_y=False, **axis_config)
            fig.update_yaxes(title_text="Web全体", row=1, col=1, secondary_y=True, showgrid=False, showline=True, linecolor='black')
            fig.update_yaxes(title_text="スコア", range=[0, 1.05], row=2, col=1, **axis_config)
            fig.update_xaxes(row=2, col=1, **axis_config, rangeslider_visible=True)

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
                                var html = '<h4 style="margin-top:0;">📅 ' + dateStr + ' の注目リンク</h4><div style="display: flex; flex-wrap: wrap; gap: 10px;">';
                                linkList.forEach(function(url, i) {
                                    url = url.trim();
                                    html += '<a href="' + url + '" target="_blank" style="text-decoration:none; color:white; background:#4a86e8; padding:8px 15px; border-radius:5px; font-weight:bold;">🔗 投稿リンク ' + (i+1) + '</a>';
                                });
                                html += '</div>';
                                display.innerHTML = html;
                                display.style.display = 'block';
                            }
                        });
                    }
                }, 100);
            })();
            </script>
            """
            script = js_template.replace('{{PLOT_ID}}', plot_div_id).replace('{{DISPLAY_ID}}', display_div_id)
            display_box = f'<div id="{display_div_id}" style="margin: 20px 80px; padding: 20px; border: 2px solid #4a86e8; border-radius: 10px; background-color: #f0f7ff; display: none; min-height: 80px;"></div>'
            plot_html = fig.to_html(include_plotlyjs='cdn', full_html=False, div_id=plot_div_id)

            full_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body style='background-color: #f8f9fa; padding: 20px;'>{plot_html}{display_box}{script}</body></html>"
            with open(os.path.join(self.output_dir, f"{book}_interactive.html"), 'w', encoding='utf-8') as f:
                f.write(full_html)
            print(f"✅ レポート生成: {book}")

    def generate_portal(self):
        """index.html を作成して全レポートを管理する"""
        if not os.path.exists(self.csv_path):
            return
        df = pd.read_csv(self.csv_path)
        books = df['book_title'].unique()
        links_html = ""

        for book in books:
            report_path = f"plots/{book}_interactive.html"
            links_html += f'<div class="card"><h3>{book}</h3><p>最新トレンド分析</p><a href="{report_path}" class="btn">レポートを見る</a></div>'

        portal_html = f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <title>Book Trend Portal</title>
            <style>
                body {{ font-family: sans-serif; background: #f4f7f6; padding: 40px; text-align: center; }}
                .container {{ display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }}
                .card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); width: 250px; }}
                .btn {{ background: #4a86e8; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <h1>📚 書籍トレンド監視ポータル</h1>
            <div class="container">{links_html}</div>
        </body>
        </html>
        """
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(portal_html)
        print("🏠 ポータル画面 (index.html) を作成しました。")