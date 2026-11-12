import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ui.services.dify_client import DifyClient, DifyClientError
from ui.services.evaluation import format_rate, load_evaluation, metric_summary


class FakeResponse:
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *_args): return False
    def read(self): return json.dumps(self.payload).encode()


class DifyClientTests(unittest.TestCase):
    @patch("ui.services.dify_client.urllib.request.urlopen")
    def test_sends_conversation_and_returns_observed_metadata(self, urlopen):
        urlopen.return_value = FakeResponse({"answer": "退款仍在处理中。", "conversation_id": "conv-1",
            "metadata": {"retriever_resources": [{"document_name": "POL-06", "content": "规则"}]}})
        result = DifyClient("http://dify/v1", "server-secret", timeout=4).chat("进度？", "conv-prev")
        request = urlopen.call_args.args[0]
        self.assertEqual(json.loads(request.data)["conversation_id"], "conv-prev")
        self.assertEqual(request.get_header("Authorization"), "Bearer server-secret")
        self.assertEqual(result.conversation_id, "conv-1")
        self.assertEqual(result.citations[0]["document_name"], "POL-06")
        self.assertTrue(result.retrieval_metadata_available)
        self.assertIsNone(result.tool_calls)

    @patch("ui.services.dify_client.urllib.request.urlopen")
    def test_distinguishes_missing_retrieval_metadata(self, urlopen):
        urlopen.return_value = FakeResponse({"answer": "无法确认。", "metadata": {}})
        result = DifyClient("http://dify/v1", "server-secret").chat("退货期限？")
        self.assertFalse(result.retrieval_metadata_available)
        self.assertEqual(result.citations, [])

    def test_missing_key_fails_without_request(self):
        with patch.dict("os.environ", {"DIFY_API_KEY": ""}), patch("ui.services.dify_client.urllib.request.urlopen") as urlopen:
            with self.assertRaises(DifyClientError): DifyClient().chat("hello")
            urlopen.assert_not_called()


class EvaluationAdapterTests(unittest.TestCase):
    def test_loads_json_and_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "results.json").write_text(json.dumps({"versions": {"v": {}}}), encoding="utf-8")
            (root / "errors.csv").write_text("case_id,task_success\nKB-01,fail\n", encoding="utf-8")
            self.assertEqual(load_evaluation(root / "results.json", root / "errors.csv")["errors"][0]["case_id"], "KB-01")

    def test_missing_metrics_are_unmeasured(self):
        self.assertEqual(format_rate({"rate": None}), "未测量")
        result = metric_summary({"evidence_hit_at_3": {"rate": None}, "latency_ms": {}})
        self.assertEqual(result["evidence_hit"], "未测量")
        self.assertEqual(result["latency"], "未测量")


if __name__ == "__main__": unittest.main()
