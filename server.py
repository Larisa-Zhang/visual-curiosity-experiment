from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import base64
import os
import csv

app = Flask(__name__)

# ✅ 启用 CORS 支持
CORS(app)

os.makedirs('screenshots', exist_ok=True)
CSV_FILE = 'record.csv'

# 可选：初始化 CSV
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
        'sessionId',
        'model',
        'actionId',
        's_t_img',
        's_t1_img',
        'after_yaw','after_pitch',
        'delta_yaw','delta_pitch',
        'init_yaw','init_pitch'   # filled on init row (actionId = -1)
    ])

@app.route('/record', methods=['POST', 'OPTIONS'])
def record():
    # ✅ 手动处理预检请求（关键）
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        return response

    # ✅ 正常 POST 请求
    data = request.get_json()
    sessionId = data.get('sessionId', '')
    after = (data.get('afterAngles') or {})
    delta = (data.get('deltaAngles') or {})
    initial = (data.get('initialAngles') or {})  # present only for init row
    modelName = data['modelName']
    s_t_img = data['s_t_img']
    s_t1_img = data['s_t1_img']
    actionId = data['actionId']
    
    if data.get('imgData1', '').startswith('data:image'):
        imgData1 = data['imgData1'].split(',')[1]
        with open(f'screenshots/{s_t_img}', 'wb') as f:
            f.write(base64.b64decode(imgData1))
    
    if data.get('imgData2', '').startswith('data:image'):
        imgData2 = data['imgData2'].split(',')[1]
        with open(f'screenshots/{s_t1_img}', 'wb') as f:
            f.write(base64.b64decode(imgData2))


    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            sessionId,
            modelName,
            actionId,
            s_t_img,
            s_t1_img,
            after.get('yaw'), after.get('pitch'),
            delta.get('yaw'), delta.get('pitch'),
            initial.get('yaw'), initial.get('pitch'),
        ])


    # ✅ 必须添加跨域头
    response = make_response(jsonify({'status': 'ok'}))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    return response

if __name__ == '__main__':
    app.run(port=5000)