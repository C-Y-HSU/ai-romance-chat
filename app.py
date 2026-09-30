# 初始化歷史訊息清單（如果沒有就建立一個空的）
if "messages" not in st.session_state:
  st.session_state.messages = []

# 渲染過去的對話訊息
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    if message["type"] == "text":
      st.markdown(message["content"])
    elif message["type"] == "image":
      st.image(message["content"], caption=message.get("caption", ""))

# 接收使用者的輸入
if user_input := st.chat_input("說點什麼甜言蜜語吧..."):
  # 1. 記錄並顯示使用者的訊息
  st.session_state.messages.append(
      {"role": "user", "type": "text", "content": user_input}
  )
  with st.chat_message("user"):
    st.markdown(user_input)

  # 2. 呼叫 Gemini 取得文字回覆
  with st.chat_message("assistant"):
    with st.spinner("正在害羞思考中..."):
      try:
        # 將 Streamlit 裡記錄的對話歷史轉換成 Gemini SDK 需要的格式
        # 這樣每次發送都會帶著完整的上下文，不會發生 client 被關閉的問題
        formatted_history = []
        for msg in st.session_state.messages[:-1]:  # 排除剛剛才加進去的最新一句
          role = "user" if msg["role"] == "user" else "model"
          if msg["type"] == "text":
            formatted_history.append(
                types.Content(
                    role=role, parts=[types.Part.from_text(text=msg["content"])]
                )
            )

        # 建立 chat session 並帶入完整的歷史紀錄與 system instruction
        chat = client.chats.create(
            model="gemini-2.5-flash",
            history=formatted_history,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt, temperature=0.8
            ),
        )

        # 發送當前訊息
        response = chat.send_message(user_input)
        reply_text = response.text

        st.markdown(reply_text)
        st.session_state.messages.append(
            {"role": "assistant", "type": "text", "content": reply_text}
        )

        # (選擇性) 觸發圖片生成的邏輯保持不變...
        if "拍張照" in user_input or "看你" in user_input or "約會" in user_input:
          st.info("📸 正在生成專屬約會畫面...")
          image_prompt = (
              f"A romantic anime style illustration of a cute companion,"
              f" based on context: {user_input}, high quality, beautiful lighting"
          )
          img_result = client.models.generate_images(
              model="imagen-3.0-generate-002",
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
