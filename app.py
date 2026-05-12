import streamlit as st
from anthropic import Anthropic
from anthropic.types import MessageStreamEvent
import os
from dotenv import load_dotenv

load_dotenv()

# ── Page config ──────────────────────────────────────────────
st.set_page_config(page_title="智能问答助手", page_icon="🤖", layout="wide")
st.title("🤖 智能问答助手")

# ── Sidebar settings ─────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 设置")

    api_key = st.text_input(
        "API Key",
        type="password",
        value=os.getenv("ANTHROPIC_API_KEY", ""),
        help="输入你的 Anthropic API Key，或通过环境变量 ANTHROPIC_API_KEY 设置",
    )

    model = st.selectbox(
        "模型",
        options=["claude-sonnet-4-6", "claude-haiku-4-5-20251001", "claude-opus-4-7"],
        index=0,
        help="选择 Claude 模型",
    )

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="控制回答的随机性，越高越有创意",
    )

    max_tokens = st.slider(
        "最大输出长度",
        min_value=256,
        max_value=8192,
        value=4096,
        step=256,
        help="限制单次回答的最大 token 数",
    )

    system_prompt = st.text_area(
        "系统提示词",
        value="你是一个乐于助人的智能助手，请用简洁清晰的中文回答用户的问题。",
        help="设定 AI 助手的行为风格",
    )

    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Initialize session state ─────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Display chat history ─────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat input ───────────────────────────────────────────────
if prompt := st.chat_input("输入你的问题..."):
    if not api_key:
        st.error("请先在侧边栏输入 API Key")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        try:
            client = Anthropic(api_key=api_key)

            with client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
            ) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        full_response += event.delta.text
                        placeholder.markdown(full_response + "▌")
                    elif event.type == "message_stop":
                        placeholder.markdown(full_response)

        except Exception as e:
            placeholder.error(f"请求失败: {e}")
            full_response = f"_[请求失败: {e}]_"

        if full_response:
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )
