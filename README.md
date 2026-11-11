# Enterprise Support Agent

基于 Dify Chatflow 的企业售后服务智能体演示项目。政策、企业、产品和订单均为虚构演示数据，不适用于真实交易；查询只读，没有真实退款、订单修改或人工转接能力。

## 功能

- 使用 Dify 知识库回答售后政策问题并展示来源。
- 查询 20 条演示订单，覆盖待付款、处理中、已发货、已完成、退款中、已退款、已取消等状态。
- 证据不足或超出授权范围时明确说明；演示订单逻辑不执行写操作。
- 提供 45 条分类测试规格、Dify API 运行脚本和按分类汇总的评估报告。

## 本机演示

已发布并验证的本机 Dify v7.11（app ID `3d9fdda7-9598-4a12-94bd-070cc2d1b5a8`）Web 入口：<http://localhost/chat/cMZWb1TkRKpbH89p>。需要本机 Dify 服务在线。该地址只在当前本机环境可访问，不是公网网站。导入前请按 `docs/dify_setup.md` 创建/绑定知识库；DSL 的知识库引用依赖目标 Dify 实例，文档数据需单独上传。

## 本地准备与验证

需要 Python 3.10 或以上。安装项目依赖（包含 Streamlit）：

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/report.py
```

## 本机 Web UI

首次配置时验证并保存 Dify 应用 Key 到当前 Windows 用户环境变量（隐藏输入；不写入项目文件）：

```powershell
.\scripts\configure_api_key.ps1
```

之后直接启动（无需再次输入 Key）：

```powershell
.\scripts\run_ui.ps1
```

配置脚本会先请求 Dify `/parameters` 验证 Key；验证失败时不会保存。启动后打开 `http://localhost:8502`。默认 Dify 地址为 `http://localhost/v1`；如需自定义，请先设置 `DIFY_BASE_URL` 再运行配置脚本。Key 只交给服务端进程，不进入网页或 Git。端口可通过参数调整，例如 `.\scripts\run_ui.ps1 -Port 8501`。

也可以自行从服务端环境变量启动：

```powershell
$env:DIFY_API_KEY = "<Dify 应用 API Key>"
$env:DIFY_BASE_URL = "http://localhost/v1"
streamlit run ui/app.py
```

评估报告页读取 `reports/evaluation_results.json` 与 `reports/eval_errors.csv`。缺失的检索、工具调用或延迟指标会显示为“未测量”。Web UI 的多轮会话只保存在 Streamlit 会话状态和 Dify 会话 ID 中，不使用数据库。

使用 Dify API 运行少量用例：

1. 在 Dify 为目标 Chatflow 创建应用 API Key。
2. 复制 `.env.example` 为 `.env` 并填写本机 Dify 地址、应用 Key。不要提交 `.env`。
3. 指定用例运行；默认最多3条，避免意外批量调用：

```powershell
python scripts/run_eval.py --case-id NA-02 --case-id CP-03 --case-id MVP-V76-ORDER
```

脚本会保存实际输入、输出、API 可返回的检索证据和客户端耗时到 `reports/live_runs.json`。未由 API 明确提供的路由、工具调用及写操作日志保持未测量。模型调用可能按 Dify/模型供应方账户配置计费。

## 目录

```text
enterprise-support-agent/
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
├── dify/support-agent.yml
├── data/knowledge/
├── data/orders.json
├── data/eval_cases.json
├── scripts/run_eval.py
├── scripts/report.py
├── ui/
│   ├── app.py
│   ├── pages/
│   └── services/
├── tests/test_orders.py
├── tests/test_ui_services.py
├── reports/evaluation.md
└── docs/
    ├── architecture.md
    ├── dify_setup.md
    └── screenshots/
```

`reports/evaluation_runs.json` 保留历史运行轨迹；视频为可选项，当前未提供演示视频。截图目录含说明，实际产品截图仍待补入。

## License

This project is provided under the [MIT License](LICENSE).
