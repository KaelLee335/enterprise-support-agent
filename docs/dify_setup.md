# Dify 导入与复现

1. 登录目标 Dify，创建知识库并上传 `data/knowledge/` 中的 10 份 Markdown 政策文档。保持其演示数据标签。
2. 导入 `dify/support-agent.yml`。DSL 引用的知识库标识来自原演示实例；如目标实例显示数据集缺失，在知识检索节点重新绑定刚创建的知识库并保存。
3. 确认模型供应方/模型名可用，运行订单查询、政策问答、无答案拒答及安全请求。
4. 当前已发布的本机应用 ID：`3d9fdda7-9598-4a12-94bd-070cc2d1b5a8`；本机入口：<http://localhost/chat/cMZWb1TkRKpbH89p>。该应用在当前 Dify 主机内发布，不代表已部署公网。
5. Dify Chatflow API 地址一般为 `<DIFY_BASE_URL>/chat-messages`，使用该应用自己的 API Key；Key 只存本机 `.env`，不能提交到版本库。
