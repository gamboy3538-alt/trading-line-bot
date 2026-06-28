import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# ตั้งค่า Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# ตั้งค่า LINE Bot Token
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

def ask_gemini(market_data):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"คุณคือผู้เชี่ยวชาญด้านการเทรด SMC (Smart Money Concepts) และวิเคราะห์กราฟทองคำ (XAUUSD) อย่างแม่นยำ นี่คือข้อมูลตลาดล่าสุดที่ได้รับมา:\n\n{market_data}\n\nกรุณาวิเคราะห์แนวโน้มตลาดตามหลักการ SMC (เช่น โครงสร้างราคา CHoCH, BOS, IDM, OB) และสรุปแผนการเทรดที่ชัดเจน สั้นกระชับ เข้าใจง่าย ส่งกลับมาเป็นภาษาไทยเพื่อแจ้งเตือนในไลน์"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการเรียก Gemini API: {str(e)}"

def send_line_message(reply_token, text):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post(url, json=payload, headers=headers)

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json()
    
    # รองรับการทดสอบสัญญาณจาก TradingView
    if body and "events" not in body:
        # ถ้าไม่มี events แสดงว่ามาจาก TradingView โดยตรง
        # สามารถประมวลผลข้อมูลแล้วส่งข้อความเข้ากลุ่ม LINE หรือบันทึกค่าได้ตามสะดวก
        return jsonify({"status": "ok", "message": "TradingView alert received"}), 200

    # รองรับ Webhook จาก LINE Developers
    events = body.get("events", [])
    for event in events:
        if event.get("type") == "message" and event["message"].get("type") == "text":
            reply_token = event["replyToken"]
            user_message = event["message"]["text"]
            
            # ส่งข้อความไปให้ Gemini วิเคราะห์
            analysis_result = ask_gemini(user_message)
            
            # ส่งผลลัพธ์กลับไปที่ LINE
            send_line_message(reply_token, analysis_result)
            
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
