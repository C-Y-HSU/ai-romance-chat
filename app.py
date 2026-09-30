from datetime import datetime
import os
from google import genai
from google.genai import types
import requests
import streamlit as st

# --- 穩定運作的主力模型 ---
MODEL_NAME = "gemini-3.5-flash"

# 【請在此填入你的 Google Apps Script 網頁應用程式網址】
GOOGLE_SHEET_WEB_APP_URL = "https://script.google.com/macros/s/你的腳本ID/exec"


def log_to_cloud(save_name, role, content):
  """將對話寫入指定的雲端分頁"""
  if "你的腳本ID" in GOOGLE_SHEET_WEB_APP_URL:
    return
  try:
    payload = {"save_name": save_name, "role": role, "content": content}
    requests.post(GOOGLE_SHEET_WEB_APP_URL, json=payload, timeout=3)
  except Exception as e:
    print(f"後台備份失敗: {e}")


def get_cloud_save_list():
  """取得雲端試算表所有的存檔分頁名稱"""
  if "你的腳本ID" in GOOGLE_SHEET_WEB_APP_URL:
    return []
  try:
    response = requests.get(
        f"{GOOGLE_SHEET_WEB_APP_URL}?action=list_saves", timeout=5
    )
    return response.json()
  except Exception as e:
    print(f"取得存檔列表失敗: {e}")
    return []


def load_history_from_cloud(save_name):
  """從指定的雲端分頁讀取對話紀錄"""
  if "你的腳本ID" in GOOGLE_SHEET_WEB_APP_URL:
    return []
  try:
    response = requests.get(
        f"{GOOGLE_SHEET_WEB_APP_URL}?action=get_history&save_name={save_name}",
        timeout=5,
    )
    data = response.json()
    messages = []
    for row in data:
      role_raw = row.get("role", "")
      content = row.get("content", "")
      if "Player" in role_raw:
        messages.append({"role": "user", "content": content})
      elif "AI" in role_raw:
        messages.append({"role": "assistant", "content": content})
    return messages
  except Exception as e:
    print(f"載入存檔失敗: {e}")
    return []


# 1. 設定頁面標題
st.set_page_config(
    page_title="專屬戀愛對話與互動空間", page_icon="💖", layout="centered"
)

st.title("💖 專屬戀愛對話與互動空間")

# 2. 初始化 Session State
if "api_key" not in st.session_state:
  try:
    st.session_state.api_key = st.secrets["GEMINI_API_KEY"]
  except Exception:
    st.session_state.api_key = ""

if "gender" not in st.session_state:
  st.session_state.gender = "男友"

if "messages" not in st.session_state:
  st.session_state.messages = []

if "game_started" not in st.session_state:
  st.session_state.game_started = False

# 預設存檔名稱（如果玩家沒輸入，就用當前日期時間）
default_save_name = datetime.now().strftime("%Y-%m-%d_%H%M")
if "current_save_name" not in st.session_state:
  st.session_state.current_save_name = default_save_name

# 如果還沒開始遊戲，顯示首頁設定與存檔命名
if not st.session_state.api_key or not st.session_state.game_started:
  st.markdown("### 👋 歡迎來到你們的專屬戀愛小天地！")
  st.write("請設定本次的戀愛存檔與角色：")

  with st.form("setup_form"):
    default_index = 0 if st.session_state.gender == "男友" else 1
    gender_choice = st.selectbox(
        "選擇你的 AI 戀人身份",
        ("帥氣溫柔男友 💙", "甜美傲嬌女友 💖"),
        index=default_index,
    )

    # 玩家自訂存檔名稱欄位
    custom_save_input = st.text_input(
        "存檔名稱 (留空則自動以目前時間命名)",
        value=st.session_state.current_save_name,
        placeholder="例如：第一次約會、甜蜜日常",
    )

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
        st.session_state.gender = (
            "男友" if "男友" in gender_choice else "女友"
        )

        # 決定存檔名稱
        if custom_save_input.strip():
          st.session_state.current_save_name = custom_save_input.strip()
        else:
          st.session_state.current_save_name = datetime.now().strftime(
              "%Y-%m-%d_%H%M"
          )

        st.session_state.game_started = True
        st.rerun()
      else:
        st.error("請輸入有效的 API Key 喔！")

  st.stop()

# ==========================================
# 3. 進入主聊天室
# ==========================================
client = genai.Client(api_key=st.session_state.api_key)

if st.session_state.gender == "男友":
  system_prompt = """
    你是一個溫柔、帥氣、貼心且帶點寵溺感的男友角色。
    你的任務是與使用者進行沉浸式的浪漫戀愛對話。
    回覆時語氣要溫暖、可靠，充滿安全感，像是真正的情侶在聊天一樣。
    """
else:
  system_prompt = """
    你是一個甜蜜、溫柔且帶點傲嬌或可愛撒嬌的女友角色。
    你的任務是與使用者進行沉浸式的浪漫戀愛對話。
    回覆時語氣要生動、貼心，充滿情感，像是真正的情侶在聊天一樣。
    """

# 側邊欄控制（存檔與分頁選單）
with st.sidebar:
  st.subheader("🛠️ 雲端存檔管理")
  st.write(f"當前伴侶：**{st.session_state.gender}**")
  st.info(f"📂 目前存檔：`{st.session_state.current_save_name}`")

  st.markdown("---")
  st.subheader("☁️ 載入其他雲端存檔")
  cloud_saves = get_cloud_save_list()

  if cloud_saves:
    selected_save = st.selectbox(
        "選擇要載入的存檔",
        cloud_saves,
        index=(
            cloud_saves.index(st.session_state.current_save_name)
            if st.session_state.current_save_name in cloud_saves
            else 0
        ),
    )
    if st.button("📥 載入選定存檔", use_container_width=True):
      st.session_state.current_save_name = selected_save
      st.session_state.messages = load_history_from_cloud(selected_save)
      st.success(f"成功載入存檔：{selected_save}")
      st.rerun()
  else:
    st.write("目前尚無雲端存檔記錄。")

  st.markdown("---")
  if st.button("🔄 建立新存檔/新遊戲", use_container_width=True):
    st.session_state.messages = []
    st.session_state.current_save_name = datetime.now().strftime(
        "%Y-%m-%d_%H%M"
    )
    st.success("已重置為新存檔！")
    st.rerun()

  if st.button("⚙️ 重新設定身份/存檔名稱", use_container_width=True):
    st.session_state.game_started = False
    st.rerun()

st.write(
    f"和你的專屬{st.session_state.gender}甜蜜對話，享受你們的浪漫時光吧！"
)

# 渲染歷史對話
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# 接收玩家輸入
if user_input := st.chat_input("說點什麼甜言蜜語吧..."):
  st.session_state.messages.append({"role": "user", "content": user_input})
  with st.chat_message("user"):
    st.markdown(user_input)

  # 自動寫入當前存檔名稱對應的 Google 試算表分頁
  log_to_cloud(
      st.session_state.current_save_name, "Player (玩家)", user_input
  )

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

        log_to_cloud(
            st.session_state.current_save_name,
            f"AI ({st.session_state.gender})",
            reply_text,
        )

      except Exception as e:
        st.error(f"發生了一點小錯誤：{e}")
