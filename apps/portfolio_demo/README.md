# AIeyu 作品集 Demo

双击 `index.html`（源码版本）或交付包中的 `AIeyu-demo.html`。无需安装、账号、网络或 API Key。

## 3 分钟演示

1. 在学习中心点击「开始 3 题体验」，自由作答并提交。
2. 查看判分和中文解析。尝试答错一题，再进入「练习薄弱点」，体验不同题目的巩固训练。
3. 返回学习中心，观察本次作答统计和错题记录。
4. 打开单词卡，翻面查看释义，标记「再练一次」或「已记住」。
5. 在项目说明查看学生产品、知识库研究进展和真实边界。

## 展示范围

这是从 AIeyu 产品流程提炼的独立离线展示界面，不是生产学生端的完整副本。题目、词卡和解析为专为演示编写的静态样例，不是历年真题，也不代表专四/专八考试难度。判分与统计根据本次点击实时计算，刷新即清空；不存在预设的学生成绩或真实学习记录。

本附件不调用生成模型。正式项目有 DeepSeek 中文解析及追问接口；这里展示的是预写解析。三套书籍知识库仍处于研究与审核阶段，未声称整体接入学生端或通过独立专家评价。

## 重建与验证

在项目根目录运行 `python scripts/build_portfolio_demo.py`，输出到 `dist/portfolio/`。打包脚本只读取本目录明确列出的演示文件，不读取数据库、环境配置、教材或研究正文。

浏览器验证：`node tests/check_portfolio_demo.cjs`。需要本机已有 Playwright；可用 `AIEYU_PLAYWRIGHT` 指定其模块路径，`AIEYU_BROWSER` 默认 `msedge`。验证过程禁用 HTTP/HTTPS 请求，直接从文件打开。

项目代码：https://github.com/reto111/AIeyu/tree/codex/tem4-clean-rebuild

作品集描述见 `docs/portfolio_demo.md`。研究数据受版权及隐私边界限制，未随 GitHub 仓库发布；研究文档中的 `data/processed/` 链接指向本地证据。
