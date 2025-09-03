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
        writer.writerow(['model', 's_t_img', 'actionId', 's_t1_img'])

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
    modelName = data['modelName']
    s_t_img = data['s_t_img']
    s_t1_img = data['s_t1_img']
    actionId = data['actionId']
    imgData1 = data['imgData1'].split(',')[1]
    imgData2 = data['imgData2'].split(',')[1]

    with open(f'screenshots/{s_t_img}', 'wb') as f:
        f.write(base64.b64decode(imgData1))
    with open(f'screenshots/{s_t1_img}', 'wb') as f:
        f.write(base64.b64decode(imgData2))

    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([modelName, s_t_img, actionId, s_t1_img])

    # ✅ 必须添加跨域头
    response = make_response(jsonify({'status': 'ok'}))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    return response

if __name__ == '__main__':
    app.run(port=5000)