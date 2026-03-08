import os
import sqlite3
import logging
from flask import Flask, render_template, request

app = Flask(__name__)

# --- ログの設定 (修正版: アドレス表示を邪魔しない設定) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(BASE_DIR, 'search.log')

# Flaskのロガーにファイル出力を追加（再起動時の干渉を防止）
if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
    ))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

DB_PATH = os.path.join(BASE_DIR, 'my_database.db')

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    code = ""
    summary = {'code': "", 'name': ""}

    if request.method == 'POST':
        code = request.form.get('code')
        summary['code'] = code
        # app.logger を使用して記録
        app.logger.info(f"Cross-tab Search (Monthly): {code}")
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # 1. 品名仕様を取得
        c.execute('SELECT "品名仕様" FROM "hinmoku_repair" WHERE "品目ＣＤ" = ? LIMIT 1', (code,))
        name_res = c.fetchone()
        if name_res:
            summary['name'] = name_res[0]
        
        # 2. 月別クロス集計クエリ (Excelコピペ用)
        query = '''
        SELECT 
            "年月",
            SUM(CASE WHEN "発注元" LIKE '工業%' THEN CAST("実績数量" AS REAL) ELSE 0 END) as qty_kogyo,
            SUM(CASE WHEN "発注元" LIKE '工業%' THEN CAST("実績金額" AS INTEGER) ELSE 0 END) as amt_kogyo,
            SUM(CASE WHEN "発注元" LIKE 'MFG%' THEN CAST("実績数量" AS REAL) ELSE 0 END) as qty_mfg,
            SUM(CASE WHEN "発注元" LIKE 'MFG%' THEN CAST("実績金額" AS INTEGER) ELSE 0 END) as amt_mfg,
            SUM(CASE WHEN "発注元" LIKE 'アクア%' THEN CAST("実績数量" AS REAL) ELSE 0 END) as qty_aqua,
            SUM(CASE WHEN "発注元" LIKE 'アクア%' THEN CAST("実績金額" AS INTEGER) ELSE 0 END) as amt_aqua,
            SUM(CAST("実績数量" AS REAL)) as qty_total,
            SUM(CAST("実績金額" AS INTEGER)) as amt_total
        FROM "hinmoku_repair"
        WHERE "品目ＣＤ" = ?
        GROUP BY "年月"
        ORDER BY "年月" ASC
        '''
        c.execute(query, (code,))
        results = c.fetchall()
        conn.close()
        
        return render_template('index.html', results=results, code=code, summary=summary)

    return render_template('index.html', results=results, code=code, summary=summary)

@app.route('/search_name', methods=['GET', 'POST'])
def search_name():
    results = []
    keyword = ""
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        app.logger.info(f"Name Partial Search (Full List): {keyword}")
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        query = 'SELECT "品目ＣＤ", "品名仕様" FROM "hinmoku_repair" WHERE "品名仕様" LIKE ?'
        c.execute(query, (f'%{keyword}%',))
        results = c.fetchall()
        conn.close()
        
    return render_template('search_name.html', results=results, keyword=keyword)

if __name__ == '__main__':
    # 外部接続を許可し、ターミナルにIPアドレスを表示させる設定
    app.run(host='0.0.0.0', port=5000, debug=True)