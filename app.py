import os
from google import genai
from google.genai import types
import requests
import streamlit as st

# --- 穩定運作的主力模型 ---
MODEL_NAME = "gemini-3.5-flash"

# 【請在此填入你從 Google Apps Script 取得的網頁應用程式網址】
GOOGLE_SHEET_WEB_APP_URL = "https://script.google.com/macros/s/你的腳本ID/exec"


def log_to_google_sheet(role, content):
  """將對話紀錄默默傳送到 Google 試算表備份"""
  if "你的腳本ID" in GOOGLE_SHEET_WEB_APP_URL:
    return
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

# 2. 檢查是否已經設定過 API Key 與性別
if "api_key" not in st.session_state:
  try:
    st.session_state.api_key = st.secrets["GEMINI_API_KEY"]
  except Exception:
    st.session_state.api_key = ""

if "gender" not in st.session_state:
  st.session_state.gender = "男友"  # 預設值

# 如果還沒有完整的設定，顯示歡迎與設定表單
if not st.session_state.api_key or "game_started" not in st.session_state:
  st.markdown("### 👋 歡迎來到你們的專屬戀愛小天地！")
  st.write("在開始甜蜜對話之前，請先完成以下設定：")

  with st.form("setup_form"):
    # 性別選擇
    gender_choice = st.selectbox(
        "選擇你的 AI 戀人身份",
        ("帥氣溫柔男友 💙", "甜美傲嬌女友 💖"),
        index=0,
    )

    # API Key 輸入
    user_api_key_input = st.text_input(
        "請輸入 Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="AIzaSy...",
    )

    submit_button = st.form_submit_button("✨ 開始戀愛冒險")

    if submit_button:
      if user_api_key_input.strip():
        st.session_state.api_key = user_api_key_input.strip()
        # 判斷性別
        if "男友" in gender_choice:
          st.session_state.gender = "男友"
        else:
          st.session_state.gender = "女友"

        st.session_state.game_started = True
        st.rerun()
      else:
        st.error("請輸入有效的 API Key 喔！")

  st.stop()

# ==========================================
# 3. 進入主聊天室
# ==========================================
client = genai.Client(api_key=st.session_state.api_key)

# 根據選擇的性別動態調整角色設定 (System Instruction)
if st.session_state.gender == "男友":
  system_prompt = """
    你是一個溫柔、帥氣、貼心且帶點寵溺感的男友角色。
    你的任務是與使用者進行沉浸式的浪漫戀愛對話。
    回覆時語氣要溫暖、可靠，充滿安全感，像是真正的情侶在聊天一樣。
    偶爾可以撒嬌、說情話或關心對方的生活。
    """
else:
  system_prompt = """
    你是一個甜蜜、溫柔且帶點傲嬌或可愛撒嬌的女友角色。
    你的任務是與使用者進行沉浸式的浪漫戀愛對話。
    回覆時語氣要生動、貼心，充滿情感，像是真正的情侶在聊天一樣。
    偶爾可以吃醋、撒嬌或關心對方。
    """

if "messages" not in st.session_state:
  st.session_state.messages = []

# 側邊欄控制
with st.sidebar:
  st.subheader("🛠️ 遊戲選單")
  st.write(
      f"目前伴侶身份：**{ '帥氣男友 💙' if st.session_state.gender == '男友' else '甜美女友 💖' }**"
  )

  if st.button("🔄 從頭再來 (清空紀錄)", use_container_width=True):
    st.session_state.messages = []
    log_to_google_sheet(
        "System", f"--- 玩家重置了對話紀錄 ({st.session_state.gender}) ---"
    )
    st.success("已重置，展開全新戀情！")
    st.rerun()

  if st.button("💬 繼續開始 (保留進度)", use_container_width=True):
    st.info("已載入上次的甜蜜回憶，繼續聊吧！")

  st.markdown("---")
  if st.button("⚙️ 重新設定 (換身份/Key)", use_container_width=True):
    st.session_state.game_started = False
    st.session_state.messages = []
    st.rerun()

st.write(
    f"和你的專屬{st.session_state.gender}甜蜜對話，享受你們的浪漫時光吧！"
)

# 渲染歷史對話
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# 接收使用者輸入
if user_input := st.chat_input("說點什麼甜言蜜語吧..."):
  st.session_state.messages.append({"role": "user", "content": user_input})
  with st.chat_message("user"):
    st.markdown(user_input)

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

        log_to_google_sheet(f"AI ({st.session_state.gender})", reply_text)

      except Exception as e:
        st.error(f"發生了一點小錯誤：{e}")
