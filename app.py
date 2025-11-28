from flask import Flask, request, jsonify
from flask_cors import CORS # 导入 CORS
import os
import openai # 假设您使用 openai 库

# 初始化 Flask 应用
app = Flask(__name__)

# ✅ 关键修复：启用 CORS，允许所有源 (origins) 访问
# 这将修复 'Fetch failed' 错误
CORS(app) 

# --- Azure OpenAI 配置 ---
# 请确保您的环境变量设置正确 (Render 环境变量)
# os.environ["AZURE_OPENAI_API_KEY"] = "YOUR_KEY" 
# os.environ["AZURE_OPENAI_ENDPOINT"] = "YOUR_ENDPOINT"

# 如果使用 openai 库，通常不需要手动设置 os.environ，
# 只需要确保 Render 上设置了这些环境变量即可。

# --- 路由和业务逻辑 ---
@app.route('/api/chat', methods=['POST'])
def chat():
    # 假设您的请求体包含 JSON 数据
    try:
        data = request.get_json()
        user_prompt = data.get('prompt')
        
        if not user_prompt:
            return jsonify({"error": "Missing prompt data"}), 400

        # --- 调用 Azure GPT-5.1 逻辑 (示例) ---
        # 这是一个简化的示例，请根据您的实际调用逻辑修改
        
        # 假设您已正确配置 Azure OpenAI SDK
        # client = openai.AzureOpenAI(
        #     api_version="2024-02-01",
        # )
        
        # response = client.chat.completions.create(
        #     model="gpt-5.1-deployment-name", # 确保这是您在 Azure 上的部署名称
        #     messages=[
        #         {"role": "system", "content": "You are a helpful assistant."},
        #         {"role": "user", "content": user_prompt}
        #     ]
        # )
        
        # gpt_response_text = response.choices[0].message.content
        
        # 临时返回一个成功消息以确认 CORS 修复
        # 请替换为您的实际 GPT 逻辑
        gpt_response_text = f"API received: '{user_prompt}'. CORS is now fixed!"

        return jsonify({"response": gpt_response_text})

    except Exception as e:
        # 捕获异常并返回 500 错误
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Render 部署不需要这一行，但本地测试需要
    # app.run(debug=True)
    pass
