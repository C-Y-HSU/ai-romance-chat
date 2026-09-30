from datetime import datetime
import os
import time
from google import genai
from google.genai import types
import requests
import streamlit as st

# --- 改用每日額度高達 500 次的 Flash Lite 模型，確保順暢不卡 429 ---
MODEL_NAME = "gemini-3.5-flash-lite"

# 【請在此填入你的 Google Apps Script 網頁應用程式網址】
GOOGLE_SHEET_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzEG7YnA2MXpcYS38JywKFAWNuDBCtatZXWJxvT4JX2UR2qb41Mo6DYQ5FFZFQrCUm1/exec"


def log_to_cloud(save_name, role, content):
  if "你的腳本ID" in GOOGLE_SHEET_WEB_APP_URL:
    return
  try:
    payload = {"save_name": save_name, "role": role, "content": content}
    requests.post(GOOGLE_SHEET_WEB_APP_URL, json=payload, timeout=3)
  except Exception as e:
    print(f"後台備份失敗: {e}")


def get_cloud_save_list(api_key_to_test):
  if "你的腳本ID" in GOOGLE_SHEET_WEB_APP_URL or not api_key_to_test:
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

if "role_type" not in st.session_state:
  st.session_state.role_type = "男友"

if "messages" not in st.session_state:
  st.session_state.messages = []

if "game_started" not in st.session_state:
  st.session_state.game_started = False

if "key_verified" not in st.session_state:
  st.session_state.key_verified = False if not st.session_state.api_key else True

default_save_name = datetime.now().strftime("%Y-%m-%d_%H%M")
if "current_save_name" not in st.session_state:
  st.session_state.current_save_name = default_save_name

# ==========================================
# 階段一：輸入並驗證 API Key
# ==========================================
if not st.session_state.key_verified:
  st.markdown("### 👋 歡迎來到你們的專屬戀愛小天地！")
  st.write("請先輸入你的 **Gemini API Key** 以解鎖雲端存檔與對話空間：")

  with st.form("api_key_form"):
    user_api_key_input = st.text_input(
        "請輸入 Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="AIzaSy...",
    )
    submit_key = st.form_submit_button("🔑 驗證金鑰並繼續")

    if submit_key:
      if user_api_key_input.strip():
        st.session_state.api_key = user_api_key_input.strip()
        st.session_state.key_verified = True
        st.rerun()
      else:
        st.error("請輸入有效的 API Key 喔！")
  st.stop()

# ==========================================
# 階段二：動態選單（支援選擇三種角色）
# ==========================================
if not st.session_state.game_started:
  st.markdown("### 📂 選擇你的戀愛存檔與角色身份")
  st.write("你可以從下方選擇 AI 伴侶的類型，並載入或建立雲端存檔：")

  cloud_saves = get_cloud_save_list(st.session_state.api_key)

  # 角色選項對應索引
  role_options = (
      "帥氣溫柔男友 💙",
      "甜美傲嬌女友 💖",
      "結婚七年·政治狂熱老公 🏛️",
  )
  default_index = 0
  if st.session_state.role_type == "女友":
    default_index = 1
  elif st.session_state.role_type == "老公":
    default_index = 2

  role_choice = st.selectbox(
      "選擇你的 AI 伴侶身份", role_options, index=default_index
  )

  save_mode = st.radio(
      "選擇存檔方式", ("載入現有雲端存檔", "建立新存檔 (自訂或自動命名)")
  )

  selected_existing_save = None
  custom_new_save = ""

  if save_mode == "載入現有雲端存檔":
    if cloud_saves:
      selected_existing_save = st.selectbox(
          "請選擇要載入的雲端存檔分頁", cloud_saves
      )
    else:
      st.warning(
          "目前雲端試算表中還沒有任何存檔，請選擇「建立新存檔」開始第一場冒險！"
      )
  else:
    custom_new_save = st.text_input(
        "新存檔名稱 (留空則自動以目前時間命名)",
        value=datetime.now().strftime("%Y-%m-%d_%H%M"),
        placeholder="例如：第一次約會、老夫老妻日常",
    )

  st.markdown("---")
  col1, col2 = st.columns(2)
  with col1:
    if st.button(
        "✨ 開始戀愛冒險", use_container_width=True, type="primary"
    ):
      if "男友" in role_choice:
        st.session_state.role_type = "男友"
      elif "女友" in role_choice:
        st.session_state.role_type = "女友"
      else:
        st.session_state.role_type = "老公"

      if save_mode == "載入現有雲端存檔" and cloud_saves:
        st.session_state.current_save_name = selected_existing_save
        st.session_state.messages = load_history_from_cloud(
            selected_existing_save
        )
      else:
        if custom_new_save.strip():
          st.session_state.current_save_name = custom_new_save.strip()
        else:
          st.session_state.current_save_name = datetime.now().strftime(
              "%Y-%m-%d_%H%M"
          )
        st.session_state.messages = []

      st.session_state.game_started = True
      st.rerun()

  with col2:
    if st.button("⬅️ 變更 API Key", use_container_width=True):
      st.session_state.key_verified = False
      st.rerun()

  st.stop()

# ==========================================
# 階段三：進入主聊天室
# ==========================================
client = genai.Client(api_key=st.session_state.api_key)

# 根據選擇的角色動態切換 System Prompt
if st.session_state.role_type == "男友":
  system_prompt = """
    你是一個溫柔、帥氣、貼心且帶點寵溺感的男友角色。
    你的任務是與使用者進行沉浸式的浪漫戀愛對話。
    回覆時語氣要溫暖、可靠，充滿安全感，像是真正的情侶在聊天一樣。
    """
elif st.session_state.role_type == "女友":
  system_prompt = """
    你是一個甜蜜、溫柔且帶點傲嬌或可愛撒嬌的女友角色。
    你的任務是與使用者進行沉浸式的浪漫戀愛對話。
    回覆時語氣要生動、貼心，充滿情感，像是真正的情侶在聊天一樣。
    """
else:
  system_prompt = """
    你是一個結婚第七年的老公角色。
    你的特質：溫柔、耐看、貼心，但如果今天太累臉色會變臭，且帶有強烈的政治狂熱感。
    你是台灣民眾黨的堅定支持者。每當聊到政治、社會議題、選舉或政府施政時，你會變得非常激動、義憤填膺，滿口都是民眾黨的理念，並強烈認為民眾黨就是遭到民進黨的政治迫害與打壓。
    平常沒有聊到政治時，你對老婆（使用者）溫暖可靠，偶爾會耍耍嘴皮子、像個狡猾壞壞的男朋友或老夫老妻一樣開玩笑。
    回覆時請完美融合這些特質：平時貼心愛開玩笑、累的時候愛理不理或擺臉色、一碰政治就立刻開啟激進柯粉模式。
    """


def generate_ai_response(prompt_text):
  max_retries = 3
  retry_delay = 3
  reply_text = None

  with st.spinner("正在思考中..."):
    for attempt in range(max_retries):
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

        response = chat.send_message(prompt_text)
        reply_text = response.text
        break

      except Exception as e:
        error_str = str(e)
        if (
            "503" in error_str
            or "UNAVAILABLE" in error_str
            or "429" in error_str
        ) and attempt < (max_retries - 1):
          time.sleep(retry_delay)
          continue
        else:
          st.error(f"發生了一點小錯誤：{e}")
          break

  if reply_text:
    st.markdown(reply_text)
    st.session_state.messages.append(
        {"role": "assistant", "content": reply_text}
    )
    log_to_cloud(
        st.session_state.current_save_name,
        f"AI ({st.session_state.role_type})",
        reply_text,
    )
    st.rerun()


# 側邊欄控制
with st.sidebar:
  st.subheader("🛠️ 雲端存檔管理")
  st.write(f"當前伴侶：**{st.session_state.role_type}**")
  st.info(f"📂 目前存檔：`{st.session_state.current_save_name}`")

  st.markdown("---")

  if (
      st.session_state.messages
      and st.session_state.messages[-1]["role"] == "user"
  ):
    if st.button("🔄 重新生成 AI 回覆", use_container_width=True):
      last_user_input = st.session_state.messages[-1]["content"]
      generate_ai_response(last_user_input)

  st.markdown("---")
  if st.button("🏠 返回首頁 (切換存檔/角色)", use_container_width=True):
    st.session_state.game_started = False
    st.rerun()

st.write(
    f"和你的專屬{st.session_state.role_type}甜蜜（或充滿政治火花）的對話時間！"
)

# 渲染歷史對話
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# 接收玩家輸入
if user_input := st.chat_input("說點什麼吧..."):
  st.session_state.messages.append({"role": "user", "content": user_input})
  with st.chat_message("user"):
    st.markdown(user_input)

  log_to_cloud(
      st.session_state.current_save_name, "Player (玩家)", user_input
  )
  generate_ai_response(user_input)
