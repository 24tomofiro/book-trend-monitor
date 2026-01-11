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
                vertical_spacing=0.15, # スライダーのために間隔を少し広げる
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
                height=800, # スライダー分、高さを少し出す
                paper_bgcolor='white', plot_bgcolor='white',
                font=dict(family=self.font_family),
                margin=dict(l=80, r=80, t=80, b=150),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            # 共通の軸設定
            axis_config = dict(showline=True, linewidth=1, linecolor='black', mirror=True, gridcolor='#eee')
            
            # 上段
            fig.update_xaxes(row=1, col=1, **axis_config)
            fig.update_yaxes(title_text="X投稿数", row=1, col=1, secondary_y=False, **axis_config)
            fig.update_yaxes(title_text="Web全体", row=1, col=1, secondary_y=True, showgrid=False, showline=True, linecolor='black')
            
            # 下段（ここにスライダーを追加）
            fig.update_yaxes(title_text="スコア", range=[0, 1.05], row=2, col=1, **axis_config)
            fig.update_xaxes(
                row=2, col=1,
                **axis_config,
                rangeslider_visible=True, # スライダーを有効化
                rangeselector=dict(
                    buttons=list([
                        dict(count=7, label="1w", step="day", stepmode="backward"),
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(step="all")
                    ])
                )
            )

            # JavaScriptテンプレート
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

            display_box = f'<div id="{display_div_id}" style="margin: 20px 80px; padding: 20px; border: 2px solid #4a86e8; border-radius: 10px; background-color: #f0f7ff; display: none; min-height: 80px;"><p style="color: #666;">（グラフの点をクリックするとここにリンクが表示されます）</p></div>'

            plot_html = fig.to_html(include_plotlyjs='cdn', full_html=False, div_id=plot_div_id)

            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8"></head>
            <body style="background-color: #f8f9fa; padding: 20px;">
                {plot_html}
                {display_box}
                {script}
            </body>
            </html>
            """

            save_path = os.path.join(self.output_dir, f"{book}_interactive.html")
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(full_html)
                
            print(f"✅ スライダーとクリック連動を両立したレポートを生成しました: {save_path}")