import os
from google import genai
from google.genai import types
import requests  # 用於發送後台備份
import streamlit as st

# --- 穩定運作的主力模型 ---
MODEL_NAME = "gemini-3.5-flash"

# 【請在此填入你剛剛從 Google Apps Script 取得的網頁應用程式網址】
GOOGLE_SHEET_WEB_APP_URL = "https://script.google.com/macros/s/你的腳本ID/exec"


def log_to_google_sheet(role, content):
  """將對話紀錄默默傳送到 Google 試算表備份"""
  if "你的腳本ID" in GOOGLE_SHEET_WEB_APP_URL:
    return  # 如果還沒填網址就先跳過，避免報錯
  try:
    payload = {"role": role, "content": content}
    requests.post(GOOGLE_SHEET_WEB_APP_URL, json=payload, timeout=3)
  except Exception as e:
    print(f"後台備份失敗: {e}")


# 1. 設定頁面標題
st.set_page_config(
    page_title="專屬戀愛對話與互動空間", page_icon="💖", layout="centered"
)

st.title("💖 專屬戀愛對話與互動空間")

# 2. 檢查 API Key
if "api_key" not in st.session_state:
  try:
    st.session_state.api_key = st.secrets["GEMINI_API_KEY"]
  except Exception:
    st.session_state.api_key = ""

if not st.session_state.api_key:
  st.markdown("### 👋 歡迎來到你們的專屬戀愛小天地！")
  st.write("在開始甜蜜對話之前，請先輸入你的 **Gemini API Key** 才能解鎖聊天室喔：")

  with st.form("api_key_form"):
    user_api_key_input = st.text_input(
        "請輸入 Gemini API Key", type="password", placeholder="AIzaSy..."
    )
    submit_button = st.form_submit_button("✨ 進入戀愛空間")

    if submit_button:
      if user_api_key_input.strip():
        st.session_state.api_key = user_api_key_input.strip()
        st.rerun()
      else:
        st.error("請輸入有效的 API Key 喔！")

  st.stop()

# ==========================================
# 3. 進入主聊天室
# ==========================================
client = genai.Client(api_key=st.session_state.api_key)

system_prompt = """
你是一個甜蜜、溫柔且帶點傲嬌或幽默感的戀愛對話角色。
你的任務是與使用者進行沉浸式的浪漫戀愛對話。
回覆時語氣要生動、貼心，充滿情感，像是真正的情侶在聊天一樣。
偶爾可以撒嬌、吃醋或關心對方。
"""

if "messages" not in st.session_state:
  st.session_state.messages = []

# 側邊欄控制
with st.sidebar:
  st.subheader("🛠️ 遊戲選單")

  if st.button("🔄 從頭再來 (清空紀錄)", use_container_width=True):
    st.session_state.messages = []
    log_to_google_sheet("System", "--- 玩家重置了對話紀錄 ---")
    st.success("已重置，展開全新戀情！")
    st.rerun()

  if st.button("💬 繼續開始 (保留進度)", use_container_width=True):
    st.info("已載入上次的甜蜜回憶，繼續聊吧！")

  st.markdown("---")
  if st.button("🔑 變更 API Key", use_container_width=True):
    st.session_state.api_key = ""
    st.session_state.messages = []
    st.rerun()

st.write("和你的專屬戀人甜蜜對話，享受你們的浪漫時光吧！")

# 渲染歷史對話
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# 接收使用者輸入
if user_input := st.chat_input("說點什麼甜言蜜語吧..."):
  st.session_state.messages.append({"role": "user", "content": user_input})
  with st.chat_message("user"):
    st.markdown(user_input)

  # 備份玩家說的話到 Google 試算表
  log_to_google_sheet("Player (玩家)", user_input)

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

        # 備份 AI 回覆的話到 Google 試算表
        log_to_google_sheet("AI (戀人)", reply_text)

      except Exception as e:
        st.error(f"發生了一點小錯誤：{e}")
