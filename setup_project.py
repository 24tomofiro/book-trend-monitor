import os

# 作成するディレクトリ構造
dirs = [
    ".github/workflows",
    "config",
    "data/raw",
    "data/processed",
    "src",
    "plots"
]

# 作成する空の雛形ファイル
files = {
    "config/books.yaml": "books:\n  - title: \"嫌われる勇気\"\n    keywords: [\"嫌われる勇気\", \"アドラー心理学\"]\n    exclude: [\"ドラマ\"]\n",
    "src/__init__.py": "",
    "src/crawler.py": "# Google APIを使った収集ロジックをここに書く\n",
    "src/processor.py": "# データ集計・ポジネガ判定ロジックをここに書く\n",
    "src/visualizer.py": "# グラフ作成ロジックをここに書く\n",
    "main.py": "import os\nfrom src.crawler import main as run_crawler\n\ndef main():\n    print('Starting Book Trend Monitor...')\n\nif __name__ == '__main__':\n    main()\n",
    "requirements.txt": "requests\npyyaml\npandas\nmatplotlib\n",
    "README.md": "# Book Trend Monitor\n特定書籍の盛り上がりを自動収集・可視化するプロジェクト\n"
}

def setup():
    # ディレクトリ作成
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"Created directory: {d}")

    # ファイル作成
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created file: {path}")

if __name__ == "__main__":
    setup()