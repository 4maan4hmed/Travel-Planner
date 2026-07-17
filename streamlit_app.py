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


def render_flight_approval(interrupt: dict) -> None:
    flight = interrupt.get("flight", {})
    st.subheader("Flight approval required")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Airline:** {flight.get('airline', 'N/A')}")
        st.markdown(f"**Flight:** {flight.get('flight_number', 'N/A')}")
        st.markdown(f"**Date:** {flight.get('departure_date', 'N/A')}")
    with col2:
        st.markdown(f"**From:** {flight.get('departure_location', 'N/A')}")
        st.markdown(f"**To:** {flight.get('arrival_location', 'N/A')}")
        st.markdown(f"**Price:** INR {flight.get('price', 'N/A')}")

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Approve", type="primary", use_container_width=True):
            _handle_resume(approved=True)
    with btn_col2:
        if st.button("Reject", use_container_width=True):
            _handle_resume(approved=False)


def _handle_resume(approved: bool) -> None:
    ok, data = api(
        "POST",
        "/chat/resume",
        json={
            "session_id": st.session_state.session_id,
            "approved": approved,
        },
    )
    if not ok:
        st.error(data)
        return

    st.session_state.pending_interrupt = None
    if data.get("assistant_message"):
        reply = data["assistant_message"]["content"]
        st.session_state.messages.append({"role": "assistant", "content": reply})
    if data.get("status") == "interrupted" and data.get("interrupt"):
        st.session_state.pending_interrupt = data["interrupt"]
    st.rerun()


# ---- Session state defaults ----
st.session_state.setdefault("base_url", "http://localhost:8000")
st.session_state.setdefault("user_id", "test-user")
st.session_state.setdefault("session_id", None)
st.session_state.setdefault("messages", [])
st.session_state.setdefault("pending_interrupt", None)


# ---- Sidebar: config + session management ----
with st.sidebar:
    st.header("Config")
    st.session_state.base_url = st.text_input("Backend URL", st.session_state.base_url)
    st.session_state.user_id = st.text_input("X-User-Id", st.session_state.user_id)

    st.divider()
    st.header("Chat session")

    if st.button("New chat", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.session_state.pending_interrupt = None
        st.success("Started a new chat. Send a message to create the session.")

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
                    st.session_state.pending_interrupt = None
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
                st.session_state.pending_interrupt = None
                st.rerun()
            else:
                st.error(data)


# ---- Main: chat UI ----
st.title("Travel Planner")

if st.session_state.session_id:
    st.caption(f"Session: {st.session_state.session_id}")
else:
    st.info("Send a message to start a new chat, or load one from the sidebar.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.session_state.pending_interrupt:
    st.warning("Approve or reject the flight below before sending another message.")
    render_flight_approval(st.session_state.pending_interrupt)
else:
    prompt = st.chat_input("Type a message...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ok, data = api(
                    "POST",
                    "/chat/message",
                    json={
                        "session_id": st.session_state.session_id,
                        "content": prompt,
                    },
                )
            if ok:
                st.session_state.session_id = data["session_id"]
                if data.get("status") == "interrupted" and data.get("interrupt"):
                    st.session_state.pending_interrupt = data["interrupt"]
                    reply = (
                        data.get("assistant_message", {}).get("content")
                        or "Waiting for your flight approval."
                    )
                    st.markdown(reply)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": reply}
                    )
                    st.rerun()
                else:
                    reply = data["assistant_message"]["content"]
                    st.markdown(reply)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": reply}
                    )
            else:
                st.error(data)
                st.session_state.messages.pop()
