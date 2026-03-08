import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    summary = {"code": "", "spec": ""}
    totals = {"qty": 0, "amount": 0}
    
    if request.method == 'POST':
        code = request.form.get('keyword', '').strip()
        conn = sqlite3.connect('my_database.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # 品名仕様を取得
        c.execute('SELECT "品名仕様" FROM "hinmoku_repair" WHERE "品目ＣＤ" = ? LIMIT 1', (code,))
        row = c.fetchone()
        if row:
            summary["code"] = code
            summary["spec"] = row["品名仕様"]

        # Excelコピペを想定したクロス集計クエリ
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

        # フッター用トータル計算
        for r in results:
            totals["qty"] += r["qty_total"]
            totals["amount"] += r["amt_total"]

        conn.close()
    
    return render_template('index.html', results=results, summary=summary, totals=totals)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
