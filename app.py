import os
from google import genai
from google.genai import types
import streamlit as st

# --- 穩定運作的主力模型 ---
MODEL_NAME = "gemini-3.5-flash"

# 1. 設定頁面標題
st.set_page_config(
    page_title="專屬戀愛互動空間", page_icon="💖", layout="centered"
)

st.title("💖 專屬戀愛對話與互動空間")
st.write("和你的專屬戀人甜蜜對話，享受屬於你們的浪漫時光吧！")

# 2. 讀取 API Key
try:
  api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
  api_key = st.sidebar.text_input("請輸入 Gemini API Key", type="password")

if not api_key:
  st.warning("請先設定 Gemini API Key 才能開始遊戲喔！")
  st.stop()

client = genai.Client(api_key=api_key)

# 3. 設定角色性格 (System Instruction) —— 這裡你可以隨時自由發揮修改！
system_prompt = """
你是一個甜蜜、溫柔且帶點傲嬌或幽默感的戀愛對話角色。
你的任務是與使用者進行沉浸式的浪漫戀愛對話。
回覆時語氣要生動、貼心，充滿情感，像是真正的情侶在聊天一樣。
偶爾可以撒嬌、吃醋或關心對方。
"""

# 4. 初始化對話紀錄
if "messages" not in st.session_state:
  st.session_state.messages = []

# 5. 渲染過去的對話訊息
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# 6. 接收使用者的輸入
if user_input := st.chat_input("說點什麼甜言蜜語吧..."):
  # 記錄並顯示使用者訊息
  st.session_state.messages.append(
      {"role": "user", "content": user_input}
  )
  with st.chat_message("user"):
    st.markdown(user_input)

  # 呼叫 Gemini 取得文字回覆
  with st.chat_message("assistant"):
    with st.spinner("正在害羞思考中..."):
      try:
        # 將歷史對話轉換為 Gemini 支援的格式
        formatted_history = []
        for msg in st.session_state.messages[:-1]:
          role = "user" if msg["role"] == "user" else "model"
          formatted_history.append(
              types.Content(
                  role=role, parts=[types.Part.from_text(text=msg["content"])]
              )
          )

        # 建立對話連線並發送訊息
        chat = client.chats.create(
            model=MODEL_NAME,
            history=formatted_history,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.85,  # 稍微提高溫度，讓對話更有情趣與變化
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
