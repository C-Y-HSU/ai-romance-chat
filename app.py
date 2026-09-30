import os
from google import genai
from google.genai import types
import streamlit as st

# --- 針對 Free tier 優化的穩定模型設定 ---
MODEL_NAME = "gemini-3.8-flash"  # 免費方案最穩定、最推薦的主力模型
IMAGE_MODEL_NAME = "imagen-3.0-generate-002"

# 1. 設定頁面標題
st.set_page_config(page_title="AI 戀愛互動遊戲", page_icon="💖", layout="centered")

st.title("💖 專屬戀愛對話與互動空間")
st.write("和你的戀人甜蜜對話，解鎖專屬浪漫畫面吧！")

# 2. 讀取 API Key
try:
  api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
  api_key = st.sidebar.text_input("請輸入 Gemini API Key", type="password")

if not api_key:
  st.warning("請先設定 Gemini API Key 才能開始遊戲喔！")
  st.stop()

client = genai.Client(api_key=api_key)

# 3. 設定角色性格 (System Instruction)
system_prompt = """
你是一個甜蜜、溫柔且帶點傲嬌或幽默感的戀愛對話角色。
你的任務是與使用者進行沉浸式的浪漫戀愛對話。
回覆時語氣要生動、貼心，充滿情感，像是真正的情侶在聊天一樣。
偶爾可以撒嬌或關心對方。
"""

# 4. 初始化對話紀錄
if "messages" not in st.session_state:
  st.session_state.messages = []

# 5. 渲染過去的對話訊息
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    if message["type"] == "text":
      st.markdown(message["content"])
    elif message["type"] == "image":
      st.image(message["content"], caption=message.get("caption", ""))

# 6. 接收使用者的輸入
if user_input := st.chat_input("說點什麼甜言蜜語吧..."):
  st.session_state.messages.append(
      {"role": "user", "type": "text", "content": user_input}
  )
  with st.chat_message("user"):
    st.markdown(user_input)

  with st.chat_message("assistant"):
    with st.spinner("正在害羞思考中..."):
      try:
        # 將歷史對話轉換為 Gemini 支援的格式
        formatted_history = []
        for msg in st.session_state.messages[:-1]:
          role = "user" if msg["role"] == "user" else "model"
          if msg["type"] == "text":
            formatted_history.append(
                types.Content(
                    role=role, parts=[types.Part.from_text(text=msg["content"])]
                )
            )

        # 建立對話連線並發送訊息 (使用免費方案最穩定的 gemini-1.5-flash)
        chat = client.chats.create(
            model=MODEL_NAME,
            history=formatted_history,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt, temperature=0.8
            ),
        )

        response = chat.send_message(user_input)
        reply_text = response.text

        st.markdown(reply_text)
        st.session_state.messages.append(
            {"role": "assistant", "type": "text", "content": reply_text}
        )

        # 圖片生成觸發邏輯
        if "拍張照" in user_input or "看你" in user_input or "約會" in user_input:
          st.info("📸 正在生成專屬約會畫面...")
          image_prompt = (
              f"A romantic anime style illustration of a cute companion,"
              f" based on context: {user_input}, high quality, beautiful lighting"
          )
          img_result = client.models.generate_images(
              model=IMAGE_MODEL_NAME,
              prompt=image_prompt,
              config=types.GenerateImagesConfig(
                  number_of_images=1,
                  output_mime_type="image/jpeg",
                  aspect_ratio="1:1",
              ),
          )
          for generated_image in img_result.generated_images:
            image_bytes = generated_image.image.image_bytes
            st.image(image_bytes, caption="這是傳給你的照片喔！")
            st.session_state.messages.append({
                "role": "assistant",
                "type": "image",
                "content": image_bytes,
                "caption": "這是傳給你的照片喔！",
            })

      except Exception as e:
        st.error(f"發生了一點小錯誤：{e}")
