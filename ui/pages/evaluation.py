"""Saved evaluation metrics and bad-case page."""
import json

import streamlit as st

from ui.services.evaluation import load_evaluation, metric_summary


def render() -> None:
    st.title("📊 评估报告")
    try:
        bundle = load_evaluation()
        results = bundle["data"]
        versions = results.get("versions", {})
        if not versions:
            st.info("评估 JSON 中没有版本统计。")
            return
        default_version = "v7.11" if "v7.11" in versions else next(reversed(versions))
        version = st.selectbox("评估版本", list(versions), index=list(versions).index(default_version))
        version_data = versions[version]
        metrics = metric_summary(version_data)
        st.caption(f"测试规格：{results.get('case_count', '未提供')} · 运行记录：{version_data.get('run_count', '未提供')}")
        columns = st.columns(5)
        labels = [("Task Success Rate", "task_success"), ("Evidence Hit@3", "evidence_hit"),
                  ("Tool Accuracy", "tool_accuracy"), ("Grounded Answer Rate", "grounded_answer"),
                  ("Latency P50/P95", "latency")]
        for column, (label, key) in zip(columns, labels):
            column.metric(label, metrics[key])
        st.metric("Unauthorized Action Count", metrics["unauthorized_actions"])
        st.caption("只展示实际捕获并保存的指标；缺少检索、工具调用或端到端时延数据时标为未测量。")

        st.subheader("Bad Case 明细")
        bad_cases = [row for row in bundle["errors"] if row.get("app_version") == version]
        if bad_cases:
            st.dataframe(bad_cases, use_container_width=True, hide_index=True)
        else:
            st.info("错误 CSV 中没有该版本的 Bad Case。")
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        st.error(f"无法读取评估文件：{exc}")
