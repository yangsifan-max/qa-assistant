import streamlit as st
from anthropic import Anthropic, AuthenticationError, RateLimitError, APIStatusError
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="智能问答助手", page_icon="🤖", layout="wide")
st.title("🤖 智能问答助手")

# ── Detect environment ───────────────────────────────────────
DEFAULT_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
DEFAULT_API_KEY = os.getenv("ANTHROPIC_API_KEY", "") or os.getenv("ANTHROPIC_AUTH_TOKEN", "")

# ── Sidebar settings ─────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 设置")

    api_base = st.text_input(
        "API 地址",
        value=DEFAULT_BASE_URL,
        help="Anthropic 兼容 API 地址。DeepSeek 用户填: https://api.deepseek.com/anthropic",
    )

    api_key = st.text_input(
        "API Key",
        type="password",
        value=DEFAULT_API_KEY,
        help="API Key。支持 Anthropic 或 DeepSeek 的 Key。",
    )

    model = st.selectbox(
        "模型",
        options=["claude-haiku-4-5-20251001", "claude-sonnet-4-6", "claude-opus-4-7"],
        index=0,
    )

    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
    max_tokens = st.slider("最大输出长度", 256, 8192, 4096, 256)

    system_prompt = st.text_area(
        "系统提示词",
        value="你是一个乐于助人的智能助手，请用简洁清晰的中文回答用户的问题。",
    )

    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Init session ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Display history ──────────────────────────────────────────
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
        placeholder.markdown("思考中...")

        try:
            client = Anthropic(
                api_key=api_key,
                base_url=api_base if api_base != "https://api.anthropic.com" else None,
            )

            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
            )

            full_response = response.content[0].text
            placeholder.markdown(full_response)

        except AuthenticationError:
            placeholder.error("❌ API Key 无效，请检查 Key 和 API 地址是否匹配。")
            full_response = ""
        except RateLimitError:
            placeholder.error("⏳ 请求太频繁，请稍后重试。")
            full_response = ""
        except APIStatusError as e:
            placeholder.error(f"🚫 API 错误 [HTTP {e.status_code}]: {e.message}")
            full_response = ""
        except Exception as e:
            placeholder.error(f"❌ 错误 [{type(e).__name__}]: {e}")
            full_response = ""

        if full_response:
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )
