"""Recall Web界面 - 截图数据服务

提供截图数据的 REST API，供 Screen Agent 和前端使用。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request, send_from_directory, send_file
from pathlib import Path
from datetime import datetime, timedelta
import base64
import json

import config
import db

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
SCREENSHOT_DIR = ROOT_DIR / config.SCREENSHOT_DIR
STATIC_DIR = Path(__file__).parent / "static" / "dist"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path='')


@app.route('/')
def index():
    """主页 - 返回 Vue 构建的 index.html"""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return send_file(index_file)
    return "前端未构建，请运行: cd web/frontend && npm install && npm run build", 404


@app.route('/api/status')
def api_status():
    """获取状态"""
    stats = db.get_stats()
    pid_file = ROOT_DIR / "logs" / "recall.pid"
    running = pid_file.exists()
    return jsonify({
        'running': running,
        'pid': pid_file.read_text() if running else None,
        **stats
    })


@app.route('/api/config', methods=['GET'])
def api_get_config():
    """获取配置 - 从数据库读取，支持热更新"""
    return jsonify(config.get_all())


@app.route('/api/config', methods=['POST'])
def api_set_config():
    """更新配置 - 写入数据库"""
    data = request.json
    config.set_all(data)
    return jsonify({'success': True, 'message': '配置已保存'})


@app.route('/api/screenshots')
def api_screenshots():
    """获取截图列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')

    with db.get_connection() as conn:
        if search:
            rows = conn.execute("""
                SELECT id, path, timestamp, ocr_text, window_title, process_name
                FROM screenshots
                WHERE ocr_text LIKE ? OR window_title LIKE ?
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """, (f'%{search}%', f'%{search}%', per_page, (page-1)*per_page)).fetchall()
        else:
            rows = conn.execute("""
                SELECT id, path, timestamp, ocr_text, window_title, process_name
                FROM screenshots
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """, (per_page, (page-1)*per_page)).fetchall()

        return jsonify([dict(row) for row in rows])


@app.route('/api/screenshot/<int:id>')
def api_screenshot_detail(id):
    """获取单个截图详情"""
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM screenshots WHERE id = ?", (id,)
        ).fetchone()
        if row:
            return jsonify(dict(row))
        return jsonify({'error': 'Not found'}), 404


@app.route('/screenshots/<path:filepath>')
def serve_screenshot(filepath):
    """提供截图文件"""
    return send_from_directory(SCREENSHOT_DIR, filepath)


# ============ Screen Agent 数据接口 ============

@app.route('/api/recent')
def api_recent():
    """获取最近截图的 OCR 摘要列表（供 Screen Agent 浏览）

    Query Parameters:
        since: ISO timestamp, 返回此时间之后的截图
        limit: int, 最多返回多少条 (默认 50)
    """
    since = request.args.get('since', '')
    limit = request.args.get('limit', 50, type=int)

    with db.get_connection() as conn:
        if since:
            rows = conn.execute("""
                SELECT id, timestamp, window_title, process_name,
                       SUBSTR(ocr_text, 1, 200) as ocr_preview, ocr_status
                FROM screenshots
                WHERE timestamp > ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (since, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT id, timestamp, window_title, process_name,
                       SUBSTR(ocr_text, 1, 200) as ocr_preview, ocr_status
                FROM screenshots
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,)).fetchall()

    return jsonify({
        'screenshots': [dict(row) for row in rows],
        'count': len(rows),
        'server_time': datetime.now().isoformat()
    })


@app.route('/api/search')
def api_search():
    """搜索截图（OCR 文本 + 窗口标题）

    Query Parameters:
        q: 搜索关键词
        hours: 往前搜索多少小时 (默认 24)
        limit: 最多返回多少条 (默认 20)
    """
    query = request.args.get('q', '')
    hours = request.args.get('hours', 24, type=int)
    limit = request.args.get('limit', 20, type=int)

    if not query:
        return jsonify({'error': '需要提供搜索关键词 q'}), 400

    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

    with db.get_connection() as conn:
        rows = conn.execute("""
            SELECT id, timestamp, window_title, process_name,
                   SUBSTR(ocr_text, 1, 300) as ocr_preview
            FROM screenshots
            WHERE timestamp > ?
              AND (ocr_text LIKE ? OR window_title LIKE ? OR process_name LIKE ?)
            ORDER BY timestamp DESC
            LIMIT ?
        """, (cutoff, f'%{query}%', f'%{query}%', f'%{query}%', limit)).fetchall()

    return jsonify({
        'results': [dict(row) for row in rows],
        'count': len(rows),
        'query': query
    })


@app.route('/api/screenshot/<int:id>/detail')
def api_screenshot_full_detail(id):
    """获取单条截图完整信息（含完整 OCR 文本）"""
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM screenshots WHERE id = ?", (id,)
        ).fetchone()
        if row:
            return jsonify(dict(row))
        return jsonify({'error': 'Not found'}), 404


@app.route('/api/screenshot/<int:id>/image')
def api_screenshot_image(id):
    """获取截图图片

    Query Parameters:
        format: 'file' (默认) 或 'base64'
    """
    fmt = request.args.get('format', 'file')

    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT path FROM screenshots WHERE id = ?", (id,)
        ).fetchone()
        if not row:
            return jsonify({'error': 'Not found'}), 404

    file_path = Path(row['path'])
    if not file_path.is_absolute():
        file_path = SCREENSHOT_DIR / file_path

    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404

    if fmt == 'base64':
        with open(file_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        return jsonify({
            'id': id,
            'image_base64': encoded,
            'content_type': 'image/jpeg'
        })

    return send_file(file_path, mimetype='image/jpeg')


@app.route('/api/activity_summary')
def api_activity_summary():
    """获取时间段内的活动统计

    Query Parameters:
        hours: 往前统计多少小时 (默认 1)
    """
    hours = request.args.get('hours', 1, type=int)
    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

    with db.get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) as count FROM screenshots WHERE timestamp > ?",
            (cutoff,)
        ).fetchone()['count']

        windows = conn.execute("""
            SELECT process_name, COUNT(*) as count
            FROM screenshots
            WHERE timestamp > ? AND process_name IS NOT NULL
            GROUP BY process_name
            ORDER BY count DESC
            LIMIT 10
        """, (cutoff,)).fetchall()

        titles = conn.execute("""
            SELECT window_title, COUNT(*) as count
            FROM screenshots
            WHERE timestamp > ? AND window_title IS NOT NULL AND window_title != ''
            GROUP BY window_title
            ORDER BY count DESC
            LIMIT 10
        """, (cutoff,)).fetchall()

    return jsonify({
        'hours': hours,
        'total_screenshots': total,
        'active_windows': {row['process_name']: row['count'] for row in windows},
        'top_titles': [{'title': row['window_title'], 'count': row['count']} for row in titles]
    })


@app.route('/api/health')
def api_health():
    """健康检查"""
    stats = db.get_stats()
    return jsonify({
        'status': 'ok',
        'service': 'recall-screenshot',
        **stats
    })


if __name__ == '__main__':
    db.init_db()
    app.run(host='127.0.0.1', port=5000, debug=True)
