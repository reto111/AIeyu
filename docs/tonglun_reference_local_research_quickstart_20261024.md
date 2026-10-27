# 《新时代俄语通论》本地研究入口

当前175个完整单元进入默认检索，127个隔离。附录仅作转录候选，不参与这里的检索。以下命令在D:\AIeyu的PowerShell中运行，均为本地操作。

先用明确关键词生成来源包，question保留研究问题，query单独指定词面检索词：

```powershell
.venv/Scripts/python.exe -X utf8 scripts/tonglun_rag.py prepare --question '词的概念意义与科学概念有哪些区别？' --query '概念意义' --limit 3 --output tmp/tonglun_packet.json
```

本次该命令已实测得到3个来源，保存在[固定示例包](../data/processed/tonglun_reference/rag/research_quickstart_packet_20261024_001.json)。来源包包含完整单元正文、卷别、PDF/印刷页码、来源及审核指纹和提示词；准备来源包不调用生成模型。这个示例的关键词由操作者提供，不能当作自动理解自然问题的实验结果。

要把某段引文缩小到具体页，可运行：

```powershell
.venv/Scripts/python.exe -X utf8 scripts/tonglun_quote_locator.py 1 v1.lexicology.ch02.sec02.unit01 '语言作为一个严谨的符号系统'
```

实测定位上册PDF43/印刷27。结果保留所有重复位置、跨页涉及页和页审核指纹；字符偏移依赖当前转录，不是PDF图像坐标。引文须保留原词形、ё和重音；页级定位的字符规则见[附录与定位说明](tonglun_reference_appendix_progress_20261024.md)。

后续若另外取得符合协议的JSON回答，可在本地核查来源与引句：

```powershell
.venv/Scripts/python.exe -X utf8 scripts/tonglun_rag.py validate --packet tmp/tonglun_packet.json --response tmp/tonglun_response.json
```

此命令需要实际存在的回答文件。本轮没有运行生成模型，也没有生成知识问答结果。核查通过只说明当前来源身份、状态和逐字引句满足约束，不说明引句足以推出主张。问题、提示词或回答的后续改动需另存实验记录，不能以引用检查代替实验协议。

正文二审见[原页材料](tonglun_reference_review_packet_20261024.md)，评分定义见[复核协议](tonglun_reference_review_protocol_20261024.md)。原转录与候选编校保持分离；未决内容和附录候选不能通过更换入口混入默认RAG。
