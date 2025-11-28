import os
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量（仅用于本地开发）
load_dotenv() 

# --- 初始化 Flask 应用 ---
app = Flask(__name__)

# --- 环境变量/密钥 ---
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_KEY = os.getenv("AZURE_KEY")
AZURE_MODEL = os.getenv("AZURE_MODEL")
AZURE_VERSION = os.getenv("AZURE_VERSION")

# --- CORS 预检处理 ---
@app.after_request
def after_request(response):
    # 允许所有来源进行跨域访问
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

# 处理 OPTIONS 预检请求
@app.route('/api/chat', methods=['OPTIONS'])
def handle_options():
    return '', 200

# --- Worker 核心逻辑：API 代理 ---
@app.route('/api/chat', methods=['POST'])
def chat_proxy():
    # 检查环境变量
    if not all([AZURE_ENDPOINT, AZURE_KEY, AZURE_MODEL, AZURE_VERSION]):
        app.logger.error("Missing Azure env variables")
        return jsonify({"error": "Missing Azure env variables"}), 500

    try:
        # 1. 读取请求体
        body = request.get_json(silent=True) or {}
    except Exception as e:
        app.logger.error(f"Error parsing request JSON: {e}")
        return jsonify({"error": "Invalid JSON body"}), 400

    # 2. 组装用户输入
    user_text = ""
    if isinstance(body.get('messages'), list):
        # 匹配您的 Worker 逻辑：将 messages 数组拼成文本
        user_text = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in body['messages']])
    elif body.get('input'):
        user_text = body['input']
    else:
        user_text = "No input provided."

    # 3. 组装 Azure URL 和 Payload
    url = f"{AZURE_ENDPOINT}/responses?api-version={AZURE_VERSION}"
    
    azure_payload = {
        "model": AZURE_MODEL,
        "input": user_text,
        "max_output_tokens": 16384
    }

    # 预留位：转发 tools
    if isinstance(body.get('tools'), list) and len(body['tools']) > 0:
        azure_payload['tools'] = body['tools']
        
    # 4. 调用 Azure GPT-5.1 Responses API
    try:
        azure_res = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "api-key": AZURE_KEY
            },
            json=azure_payload,
            timeout=60 # 设置超时时间
        )
        
        azure_res.raise_for_status() # 检查 HTTP 错误

        result = azure_res.json()
        
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Azure API request failed: {e}")
        return jsonify({"error": f"Azure API request failed: {e}"}), 503
    
    # 5. 关键修正：从 result 里稳健抽出文本
    output = extract_azure_text(result)

    if not output or output.strip() == "":
        return jsonify({"error": "Empty response from Azure", "raw": result}), 500

    # 6. 尝试解析并返回结果（匹配您 Worker 的逻辑）
    try:
        # 尝试当 JSON 解析（例如工具输出）
        parsed = json.loads(output)
        return jsonify(parsed) # Flask 默认会添加 JSON 头部
    except json.JSONDecodeError:
        # 解析失败就当纯文本返回
        response = app.make_response(output)
        response.headers['Content-Type'] = 'text/plain'
        return response

    except Exception as e:
        app.logger.error(f"Internal processing error: {e}")
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------
# 辅助函数：从 Azure Responses API 的结果里提取人类可读文本
# ----------------------------------------------------
def extract_azure_text(result):
    if not result:
        return ""

    # 1) 直接有 output_text 字段
    if isinstance(result.get("output_text"), str) and result["output_text"].strip():
        return result["output_text"]

    # 2) 标准 Responses API：output 是一个数组
    if isinstance(result.get("output"), list):
        for item in result["output"]:
            if isinstance(item, dict) and isinstance(item.get("content"), list):
                txt = "".join([
                    part.get("text") or part.get("output_text") or part.get("content") or ""
                    for part in item["content"] if isinstance(part, dict)
                ])
                if txt.strip():
                    return txt
    
    # 3) 兼容老的 chat/completions
    if isinstance(result.get("choices"), list) and result["choices"] and result["choices"][0].get("message"):
        msg = result["choices"][0]["message"]
        if isinstance(msg.get("content"), str):
            return msg["content"]
        if isinstance(msg.get("content"), list):
             return "".join([part.get("text") or "" for part in msg["content"] if isinstance(part, dict)])

    return ""

# 本地调试启动点
if __name__ == '__main__':
    # 默认运行在 5000 端口
    app.run(host='0.0.0.0', port=5000, debug=True)
