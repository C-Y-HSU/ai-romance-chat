import os
from google import genai
from google.genai import types
import streamlit as st

# --- 穩定運作的主力模型 ---
MODEL_NAME = "gemini-3.5-flash"

# 1. 設定頁面標題
st.set_page_config(
    page_title="專屬戀愛對話與互動空間", page_icon="💖", layout="centered"
)

st.title("💖 專屬戀愛對話與互動空間")

# 2. 檢查是否已經有 API Key (優先讀取 Secrets，若無則透過畫面輸入)
if "api_key" not in st.session_state:
  try:
    st.session_state.api_key = st.secrets["GEMINI_API_KEY"]
  except Exception:
    st.session_state.api_key = ""

# 如果還沒有 API Key，顯示漂亮的歡迎與輸入表單
if not st.session_state.api_key:
  st.markdown("### 👋 歡迎來到你們的專屬戀愛小天地！")
  st.write("在開始甜蜜對話之前，請先輸入你的 **Gemini API Key** 才能解鎖聊天室喔：")

  # 用 Form 讓使用者輸入並按下按鈕確認
  with st.form("api_key_form"):
    user_api_key_input = st.text_input(
        "請輸入 Gemini API Key", type="password", placeholder="AIzaSy..."
    )
    submit_button = st.form_submit_button("✨ 進入戀愛空間")

    if submit_button:
      if user_api_key_input.strip():
        st.session_state.api_key = user_api_key_input.strip()
        st.rerun()  # 重新整理畫面進入聊天室
      else:
        st.error("請輸入有效的 API Key 喔！")

  st.stop()  # 阻斷後續程式碼，直到取得 API Key 為止

# ==========================================
# 3. 已經取得 API Key，正式進入聊天室主畫面
# ==========================================
client = genai.Client(api_key=st.session_state.api_key)

# 設定角色性格 (System Instruction)
system_prompt = """
你是一個甜蜜、溫柔且帶點傲嬌或幽默感的戀愛對話角色。
你的任務是與使用者進行沉浸式的浪漫戀愛對話。
回覆時語氣要生動、貼心，充滿情感，像是真正的情侶在聊天一樣。
偶爾可以撒嬌、吃醋或關心對方。
"""

# 初始化對話紀錄
if "messages" not in st.session_state:
  st.session_state.messages = []

# 提供一個按鈕可以隨時「重新設定 API Key」或清空重來
with st.sidebar:
  if st.button("🔄 重新設定 API Key"):
    st.session_state.api_key = ""
    st.session_state.messages = []
    st.rerun()

st.write("和你的專屬戀人甜蜜對話，享受屬於你們的浪漫時光吧！")

# 渲染過去的對話訊息
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# 接收使用者的輸入
if user_input := st.chat_input("說點什麼甜言蜜語吧..."):
  st.session_state.messages.append({"role": "user", "content": user_input})
  with st.chat_message("user"):
    st.markdown(user_input)

  with st.chat_message("assistant"):
    with st.spinner("正在害羞思考中..."):
      try:
        formatted_history = []
        for msg in st.session_state.messages[:-1]:
          role = "user" if msg["role"] == "user" else "model"
          formatted_history.append(
              types.Content(
                  role=role, parts=[types.Part.from_text(text=msg["content"])]
              )
          )

        chat = client.chats.create(
            model=MODEL_NAME,
            history=formatted_history,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt, temperature=0.85
            ),
        )

        response = chat.send_message(user_input)
        reply_text = response.text

        st.markdown(reply_text)
        st.session_state.messages.append(
            {"role": "assistant", "content": reply_text}
        )

      except Exception as e:
        st.error(f"發生了一點小錯誤：{e}")
