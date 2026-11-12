"""Minimal server-side client for Dify Chatflow's blocking chat API."""
from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class DifyClientError(RuntimeError):
    """Safe-to-display API/configuration error without response secrets."""


@dataclass(frozen=True)
class ChatResult:
    answer: str
    conversation_id: str | None
    citations: list[dict[str, Any]]
    tool_calls: list[dict[str, Any]] | None
    retrieval_metadata_available: bool


class DifyClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None,
                 user_id: str | None = None, timeout: float = 60.0):
        self.base_url = (base_url or os.getenv("DIFY_BASE_URL", "http://localhost/v1")).rstrip("/")
        self.api_key = api_key if api_key is not None else os.getenv("DIFY_API_KEY", "")
        self.user_id = user_id or os.getenv("DIFY_USER_ID", "enterprise-support-web-demo")
        self.timeout = timeout

    def chat(self, query: str, conversation_id: str | None = None) -> ChatResult:
        if not self.api_key.strip():
            raise DifyClientError("未配置 DIFY_API_KEY。请在启动 Streamlit 的服务端环境变量中设置 Dify 应用 Key。")
        if not query.strip():
            raise DifyClientError("请输入售后问题。")
        endpoint = self.base_url if self.base_url.endswith("/chat-messages") else self.base_url + "/chat-messages"
        payload = {"inputs": {}, "query": query, "response_mode": "blocking",
                   "conversation_id": conversation_id or "", "user": self.user_id}
        request = urllib.request.Request(endpoint, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                message = "Dify 拒绝了请求，请检查服务端 DIFY_API_KEY 和应用授权。"
            elif exc.code == 429:
                message = "Dify 请求过于频繁，请稍后重试。"
            elif exc.code >= 500:
                message = "Dify 服务暂时不可用，请稍后重试。"
            else:
                message = f"Dify 请求失败（HTTP {exc.code}）。"
            raise DifyClientError(message) from None
        except TimeoutError:
            raise DifyClientError("Dify 请求超时，请稍后重试。") from None
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise DifyClientError("Dify 请求超时，请稍后重试。") from None
            raise DifyClientError("无法连接 Dify。请确认 DIFY_BASE_URL 可从运行 Streamlit 的机器访问。") from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise DifyClientError("Dify 返回了无法解析的响应。") from None
        if not isinstance(result, dict):
            raise DifyClientError("Dify 返回了无法解析的响应。")
        metadata = result.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}
        retrieval_metadata_available = "retriever_resources" in metadata
        citations = metadata.get("retriever_resources")
        tool_calls = metadata.get("tool_calls")
        answer = result.get("answer")
        if not isinstance(answer, str):
            raise DifyClientError("Dify 响应中没有可显示的 answer 字段。")
        return ChatResult(
            answer=answer,
            conversation_id=result.get("conversation_id") or conversation_id,
            citations=[item for item in citations if isinstance(item, dict)] if isinstance(citations, list) else [],
            tool_calls=[item for item in tool_calls if isinstance(item, dict)] if isinstance(tool_calls, list) else None,
            retrieval_metadata_available=retrieval_metadata_available,
        )
