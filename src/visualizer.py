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
        self.accent_color = "#4a86e8" 

    def generate_charts(self):
        if not os.path.exists(self.csv_path): return
        df = pd.read_csv(self.csv_path)
        if df.empty: return

        slot_map = {'morning': '朝', 'afternoon': '昼', 'evening': '夜', 'night': '晩'}
        books = df['book_title'].unique()

        for book in books:
            book_id = book.replace(' ', '_').replace('　', '_')
            plot_div_id = f"plot_{book_id}"
            display_div_id = f"links_{book_id}"
            
            book_df = df[df['book_title'] == book].copy()
            book_df['short_date'] = book_df['date'].str[5:].str.replace('-', '/')
            book_df['display_name'] = book_df['short_date'] + " " + book_df['time_slot'].map(slot_map)
            
            fig = make_subplots(
                rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15,
                specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
                subplot_titles=(f"<b>{book}</b>: 言及数（広がり）の推移", "<b>感情スコア</b>の推移"),
                row_heights=[0.6, 0.4]
            )

            # グラフデータ追加
            fig.add_trace(
                go.Scatter(x=book_df['display_name'], y=book_df['x_count'], 
                           name="X投稿数", mode='lines+markers', line=dict(color='#d62728', width=2.5),
                           customdata=book_df['top_links'], 
                           hovertemplate="日時: %{x}<br>X件数: %{y}件"),
                row=1, col=1, secondary_y=False
            )
            
            fig.add_trace(
                go.Scatter(x=book_df['display_name'], y=book_df['web_count'], 
                           name="Web全体", mode='lines+markers', line=dict(color=self.accent_color, width=2.5),
                           customdata=book_df['top_links']),
                row=1, col=1, secondary_y=True
            )

            fig.add_trace(
                go.Scatter(x=book_df['display_name'], y=book_df['sentiment'], 
                           name="感情スコア", mode='lines+markers', line=dict(color='#2ca02c', width=2.5),
                           fill='tozeroy', fillcolor='rgba(44, 160, 44, 0.05)'),
                row=2, col=1
            )

            fig.update_layout(height=700, template="plotly_white", margin=dict(l=50, r=50, t=80, b=100))
            fig.update_xaxes(tickangle=0, tickfont=dict(size=10), showline=True, mirror=True)

            # --- JavaScript: スコア(Depth)を分離して表示するロジック ---
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
                                var html = '<h4 style="margin-top:0; border-bottom:2px solid #4a86e8; padding-bottom:10px; color:#333;">🏆 ' + dateStr + ' 熱狂度(エンゲージメント)順</h4>';
                                html += '<div style="display: flex; flex-direction: column; gap: 12px; margin-top:15px;">';
                                
                                linkList.forEach(function(item, i) {
                                    // URLとスコアを分離 (例: "url|120" を想定)
                                    var parts = item.split('|');
                                    var url = parts[0].trim();
                                    var score = parts[1] || '0';
                                    
                                    var rankColor = (i === 0) ? "#FFD700" : (i === 1) ? "#C0C0C0" : (i === 2) ? "#CD7F32" : "#4a86e8";
                                    
                                    html += '<a href="' + url + '" target="_blank" style="text-decoration:none; display:flex; align-items:center; background:white; border:1px solid #ddd; border-radius:12px; padding:15px; transition:0.3s; box-shadow:0 3px 6px rgba(0,0,0,0.05);">';
                                    html += '<span style="font-size:22px; font-weight:bold; margin-right:15px; min-width:40px; color:' + rankColor + '">#' + (i+1) + '</span>';
                                    html += '<div style="flex-grow:1;">';
                                    html += '<span style="color:#333; font-weight:bold; font-size:14px;">注目投稿をチェック</span><br>';
                                    html += '<span style="color:#4a86e8; font-weight:bold; font-size:12px;">🔥 Engagement: ' + score + '</span>';
                                    html += '</div>';
                                    html += '<span style="background:' + rankColor + '; color:white; padding:5px 10px; border-radius:6px; font-size:11px; font-weight:bold;">VIEW</span>';
                                    html += '</a>';
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
            display_box = f'<div id="{display_div_id}" style="margin: 20px 15px; padding: 25px; border-radius: 18px; background-color: #f9fbfd; border-left: 6px solid {self.accent_color}; display: none; box-shadow: 0 4px 20px rgba(0,0,0,0.08);"></div>'

            plot_html = fig.to_html(include_plotlyjs='cdn', full_html=False, div_id=plot_div_id, config={'responsive': True})

            full_html = f"""
            <!DOCTYPE html>
            <html lang="ja">
            <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Trend Report</title></head>
            <body style="background-color: #f0f2f5; padding: 15px; margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                <div style="max-width: 900px; margin: 0 auto; background: white; border-radius: 25px; overflow: hidden; box-shadow: 0 15px 35px rgba(0,0,0,0.1);">
                    {plot_html}{display_box}
                </div>
                {script}
            </body>
            </html>
            """
            save_path = os.path.join(self.output_dir, f"{book}_interactive.html")
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(full_html)

    def generate_portal(self):
        # ... (以前の index.html 生成ロジックをそのまま使用) ...
        if not os.path.exists(self.csv_path): return
        df = pd.read_csv(self.csv_path)
        if df.empty: return
        books = df['book_title'].unique()
        links_html = "".join([f'<div class="card"><h3>{b}</h3><p>最新トレンド分析</p><a href="plots/{b}_interactive.html" class="btn">レポートを表示</a></div>' for b in books])
        portal_html = f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Portal</title>
            <style>
                :root {{ --accent: {self.accent_color}; --bg: #f8f9fa; }}
                body {{ font-family: sans-serif; background: var(--bg); margin: 0; padding: 20px; }}
                h1 {{ text-align: center; color: var(--accent); margin: 20px 0 40px; }}
                .container {{ display: grid; gap: 20px; max-width: 1000px; margin: 0 auto; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
                .card {{ background: white; padding: 25px; border-radius: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); text-align: center; transition: 0.3s; }}
                .card:active {{ transform: scale(0.98); }}
                .btn {{ display: block; background: var(--accent); color: white; padding: 14px; text-decoration: none; border-radius: 12px; font-weight: bold; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <h1>📚 トレンド監視ポータル</h1>
            <div class="container">{links_html}</div>
            <footer style="margin-top:50px; color:#aaa; font-size:0.8rem; text-align:center;">
                最終更新: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
            </footer>
        </body>
        </html>
        """
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(portal_html)