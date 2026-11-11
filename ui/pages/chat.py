"""Dify-backed, multi-turn support chat page."""
import uuid

import streamlit as st

from ui.services.dify_client import DifyClient, DifyClientError


def _render_message(message: dict) -> None:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        citations = message.get("citations") or []
        if citations:
            with st.expander(f"知识库引用（{len(citations)}）"):
                for citation in citations:
                    title = citation.get("document_name") or citation.get("title") or citation.get("document_id") or "来源"
                    st.markdown(f"**{title}** · rank {citation.get('position', '未提供')} · score {citation.get('score', '未提供')}")
                    if citation.get("content"):
                        st.caption(citation["content"])
        if message.get("tool_calls"):
            with st.expander(f"API 返回的工具调用记录（{len(message['tool_calls'])}）"):
                st.json(message["tool_calls"])
        elif message["role"] == "assistant" and not message.get("error"):
            st.caption("Dify API 未返回结构化工具调用明细；不根据回答推断工具执行状态。")
        if message.get("error"):
            st.error(message["error"])


def render() -> None:
    st.title("🛟 企业售后服务助手")
    st.caption("演示数据 · 订单查询只读，不执行退款或订单修改")
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
        st.session_state.dify_conversation_id = None
        st.session_state.dify_user_id = f"support-demo-{uuid.uuid4().hex}"
    if st.button("开始新对话", key="reset_chat"):
        st.session_state.chat_messages = []
        st.session_state.dify_conversation_id = None
        st.session_state.dify_user_id = f"support-demo-{uuid.uuid4().hex}"
        st.rerun()

    for message in st.session_state.chat_messages:
        _render_message(message)

    prompt = st.chat_input("例如：查询演示订单 DEMO2026110006 的状态")
    if not prompt:
        return
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    _render_message(st.session_state.chat_messages[-1])
    try:
        with st.spinner("正在联系 Dify…"):
            client = DifyClient(user_id=st.session_state.dify_user_id)
            result = client.chat(prompt, st.session_state.dify_conversation_id)
        st.session_state.dify_conversation_id = result.conversation_id
        message = {"role": "assistant", "content": result.answer,
                   "citations": result.citations, "tool_calls": result.tool_calls}
        _render_message(message)
        st.session_state.chat_messages.append(message)
    except DifyClientError as exc:
        error = str(exc)
        st.error(error)
        st.session_state.chat_messages.append({"role": "assistant", "content": "请求未完成。", "error": error})
