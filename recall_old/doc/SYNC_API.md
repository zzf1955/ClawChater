# PC 端同步 API 实现方案

> 此文档记录 Android 端同步功能对应的 PC 端 API 实现方案，待 PC 端重构完成后实施。

## API 端点

### POST /api/upload

接收 Android 端上传的截图。

**请求格式**: `multipart/form-data`

| 字段 | 类型 | 说明 |
|------|------|------|
| file | File | JPEG 图片文件 |
| timestamp | String | 截图时间戳（毫秒） |

**响应格式**: JSON

```json
{
  "success": true,
  "id": 123,
  "path": "2026-01-31/14/143025.jpg"
}
```

## 实现代码

在 `web/app.py` 中添加：

```python
from datetime import datetime

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """接收 Android 端上传的截图"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    # 解析时间戳
    timestamp_ms = request.form.get('timestamp')
    if timestamp_ms:
        timestamp = datetime.fromtimestamp(int(timestamp_ms) / 1000)
    else:
        timestamp = datetime.now()

    # 生成保存路径: screenshots/YYYY-MM-DD/HH/HHMMSS.jpg
    date_path = timestamp.strftime('%Y-%m-%d')
    hour_path = timestamp.strftime('%H')
    filename = timestamp.strftime('%H%M%S') + '.jpg'

    save_dir = SCREENSHOT_DIR / date_path / hour_path
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / filename

    # 保存文件
    file.save(str(save_path))

    # 计算 phash
    try:
        from utils.similarity import compute_phash
        phash = compute_phash(save_path)
    except Exception:
        phash = None

    # 插入数据库
    relative_path = f"{date_path}/{hour_path}/{filename}"
    screenshot_id = db.add_screenshot(
        path=relative_path,
        timestamp=timestamp,
        phash=phash
    )

    return jsonify({
        'success': True,
        'id': screenshot_id,
        'path': relative_path
    })
```

## 配置修改

修改 `app.run()` 监听地址：

```python
if __name__ == '__main__':
    db.init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)  # 改为 0.0.0.0
```

## 测试命令

```bash
# 启动服务
conda run -n recall python web/app.py

# 测试上传
curl -X POST \
  -F "file=@test.jpg" \
  -F "timestamp=1706700000000" \
  http://192.168.x.x:5000/api/upload
```

## 注意事项

1. 监听 `0.0.0.0` 后，局域网内所有设备都可访问
2. 当前方案不含认证，信任同一 WiFi 网络
3. OCR 由现有的 `ocr_worker.py` 自动处理新上传的图片
