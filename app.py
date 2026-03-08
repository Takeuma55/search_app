import os
import sqlite3
import logging
from flask import Flask, render_template, request

app = Flask(__name__)

# --- ログの設定 ---
# 誰が何を検索したかを search.log に記録します
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(BASE_DIR, 'search.log')
logging.basicConfig(filename=log_path, level=logging.INFO, 
                    format='%(asctime)s %(levelname)s: %(message)s')

DB_PATH = os.path.join(BASE_DIR, 'my_database.db')

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    code = ""
    # エラー回避のため初期値を設定
    summary = {'code': "", 'name': ""}

    if request.method == 'POST':
        code = request.form.get('code')
        summary['code'] = code
        logging.info(f"Cross-tab Search (Monthly): {code}")
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # 1. 品名仕様を取得 (hinmoku_repairテーブルから)
        c.execute('SELECT "品名仕様" FROM "hinmoku_repair" WHERE "品目ＣＤ" = ? LIMIT 1', (code,))
        name_res = c.fetchone()
        if name_res:
            summary['name'] = name_res[0]
        
        # 2. Excelコピペ用の月別クロス集計クエリ
        # 各発注元（工業、MFG、アクア）ごとの実績を年月で集計します
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

    # GET（初期表示）
    return render_template('index.html', results=results, code=code, summary=summary)

# --- 新機能: 品名あいまい検索 ---
@app.route('/search_name', methods=['GET', 'POST'])
def search_name():
    results = []
    keyword = ""
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        logging.info(f"Name Partial Search: {keyword}")
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # LIKE句を使って、キーワードが含まれる資材を最大50件抽出します
        query = 'SELECT "品目ＣＤ", "品名仕様" FROM "hinmoku_repair" WHERE "品名仕様" LIKE ?'
        c.execute(query, (f'%{keyword}%',))
        results = c.fetchall()
        conn.close()
        
    return render_template('search_name.html', results=results, keyword=keyword)

if __name__ == '__main__':
    # 開発時は debug=True にしておくことで、修正が即座に反映されます
    app.run(host='0.0.0.0', port=5000, debug=True)