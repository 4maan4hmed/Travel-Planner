"""Simple Streamlit frontend for manually testing the Travel Planner backend.

Run the FastAPI backend first, then:
    streamlit run streamlit_app.py
"""

import requests
import streamlit as st

st.set_page_config(page_title="Travel Planner Tester", layout="centered")


def get_headers() -> dict:
    return {"X-User-Id": st.session_state.user_id}


def api(method: str, path: str, **kwargs):
    """Call the backend and return (ok, data_or_error)."""
    url = f"{st.session_state.base_url.rstrip('/')}{path}"
    try:
        resp = requests.request(
            method,
            url,
            headers=get_headers(),
            timeout=120,
            **kwargs,
        )
    except requests.RequestException as exc:
        return False, f"Request failed: {exc}"

    try:
        data = resp.json()
    except ValueError:
        data = resp.text

    if not resp.ok:
        return False, f"{resp.status_code}: {data}"
    return True, data


# ---- Session state defaults ----
st.session_state.setdefault("base_url", "http://localhost:8000")
st.session_state.setdefault("user_id", "test-user")
st.session_state.setdefault("session_id", None)
st.session_state.setdefault("messages", [])


# ---- Sidebar: config + session management ----
with st.sidebar:
    st.header("Config")
    st.session_state.base_url = st.text_input("Backend URL", st.session_state.base_url)
    st.session_state.user_id = st.text_input("X-User-Id", st.session_state.user_id)

    st.divider()
    st.header("Chat session")

    if st.button("Create new chat", use_container_width=True):
        ok, data = api("POST", "/chat/create", json={})
        if ok:
            st.session_state.session_id = data["session_id"]
            st.session_state.messages = []
            st.success(f"Created {data['session_id']}")
        else:
            st.error(data)

    ok, data = api("GET", "/chat/list")
    if ok:
        chats = data.get("chats", [])
        options = [c["session_id"] for c in chats]
        if options:
            current = st.session_state.session_id
            index = options.index(current) if current in options else 0
            selected = st.selectbox("Load existing chat", options, index=index)
            if st.button("Load", use_container_width=True):
                ok2, chat = api("GET", f"/chat/{selected}")
                if ok2:
                    st.session_state.session_id = selected
                    st.session_state.messages = chat.get("messages", [])
                    st.rerun()
                else:
                    st.error(chat)
        else:
            st.caption("No existing chats for this user.")
    else:
        st.warning(data)

    if st.session_state.session_id:
        if st.button("Delete current chat", use_container_width=True):
            ok, data = api("DELETE", f"/chat/{st.session_state.session_id}")
            if ok:
                st.session_state.session_id = None
                st.session_state.messages = []
                st.rerun()
            else:
                st.error(data)


# ---- Main: chat UI ----
st.title("Travel Planner")

if st.session_state.session_id:
    st.caption(f"Session: {st.session_state.session_id}")
else:
    st.info("Create or load a chat from the sidebar to start.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input(
    "Type a message...",
    disabled=st.session_state.session_id is None,
)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            ok, data = api(
                "POST",
                f"/chat/{st.session_state.session_id}/message",
                json={"content": prompt},
            )
        if ok:
            reply = data["assistant_message"]["content"]
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        else:
            st.error(data)
            st.session_state.messages.pop()
