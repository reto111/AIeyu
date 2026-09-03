# Aliyun Windows ECS Deployment

> 本文档记录 AIeyu 在阿里云 Windows Server 试用服务器上的小范围测试部署流程。

## 1. 当前目标

把本地 AIeyu 原型部署到阿里云 ECS，让学生可以通过公网地址访问网页测试。

当前服务器信息由用户截图确认：

- 云厂商：阿里云 ECS
- 系统：Windows Server 2022 数据中心版 64 位中文版
- 配置：2 vCPU / 4 GiB
- 用途：小范围学生测试

## 2. 推荐部署路线

```text
本地 Git 提交
-> GitHub 私有仓库
-> 服务器 git clone
-> 服务器复制本地数据库和 .env
-> 启动学生端服务
-> 开放安全组和 Windows 防火墙端口
```

## 3. GitHub 仓库要求

建议创建：

```text
Reto111/AIeyu
```

必须选择：

```text
Private
```

不要在 GitHub 网页初始化 README、.gitignore 或 License，避免和本地仓库历史冲突。

当前 `.gitignore` 已排除：

- `.env`
- SQLite 数据库
- 原始 PDF
- 处理后的题库文件
- 虚拟环境和缓存

## 4. 服务器需要安装

Windows Server 上需要安装：

- Git for Windows
- Python 3.11 或 3.12
- 可选：VS Code

进入项目目录后安装网页端依赖：

```powershell
python -m pip install -r requirements-web.txt
```

其中 `pymorphy3` 用于俄语词形还原；缺少它时网页仍可能启动，但发布前健康检查不会通过。

## 5. 服务器启动方式

在服务器项目目录中运行：

```powershell
python scripts\serve_student_app.py --host 0.0.0.0 --port 8765
```

注意：服务器上不能只监听 `127.0.0.1`，否则外部访问不到。

## 6. 必须单独复制的本地文件

这些文件不会进入 GitHub，需要手动复制到服务器：

```text
database\russian_ai_tutor.sqlite
.env
```

原因：

- 数据库含题库与测试数据。
- `.env` 含 DeepSeek API Key。

## 7. 开放访问

需要开放两层端口：

1. 阿里云安全组：TCP `8765`
2. Windows 防火墙：TCP `8765`

开放后访问：

```text
http://服务器公网IP:8765/
```

## 8. 测试期注意事项

- 不要公开服务器 IP、账号密码、远程连接凭证或 API Key。
- 当前已接入轻量登录系统：学生使用“姓名 + 密码”注册/登录，密码最少 8 位。
- 学生登录后只能读取自己的错题、单词进度、AI 对话等个人数据。
- 登录状态保存在浏览器 Cookie 中；服务器必须使用同一个 `database\russian_ai_tutor.sqlite` 才能保留学生账号和学习记录。
- 小范围测试仍建议只发给可信学生，因为当前还没有 HTTPS、找回密码、管理员后台和风控。
- 真实商业化前需要升级 HTTPS、邮箱/手机号验证、密码找回、管理员权限、调用额度限制和日志监控。

## 9. 服务器更新包使用方式

更新包会排除 `.env` 和 `database\russian_ai_tutor.sqlite`，因此不会自动覆盖服务器密钥和学生数据。上传后按以下顺序操作：

1. 停止当前 Python 服务。
2. 备份服务器数据库：

```powershell
Copy-Item .\database\russian_ai_tutor.sqlite .\database\russian_ai_tutor_before_update.sqlite
```

3. 将更新包解压并覆盖到项目目录，保留服务器原有的 `.env` 和 `database\russian_ai_tutor.sqlite`。
4. 依次执行当前版本的确定性内容修正和知识点重标：

```powershell
python -B scripts\apply_question_quality_fixes.py
python -B scripts\tag_question_knowledge_points.py --apply
python -B scripts\apply_vocabulary_quality_fixes.py
```

这些脚本都会在写入前备份数据库，只修改题目文本、知识点关系和已确认词义，不删除学生账号、作答、错题或单词进度。请保持上述顺序：先修题目，再按修正后的题目重标，最后修词义。

5. 重新启动服务：

```powershell
python scripts\serve_student_app.py --host 0.0.0.0 --port 8765
```

这些修正脚本可重复执行；再次运行会重写相同的确定性结果，不会删除学生账号和学习记录。

## 10. 发布前一键验收

服务启动后，另开一个 PowerShell 窗口执行：

```powershell
cd C:\AIeyu
python -B scripts\check_mvp_readiness.py --base-url http://127.0.0.1:8765
```

脚本会检查数据库完整性、必要数据表、专四/专八正式题量和词量、题库高风险项、词库基础异常、静态文件、DeepSeek 配置、俄语词形还原、网页健康状态、核心接口和自动化回归测试。

- 全部显示 `PASS` 且进程退出码为 `0` 时才可发布。
- 任一项显示 `FAIL` 时先修复，不要直接对外开放新版本。
- 完整结果保存在 `data\processed\health\mvp_readiness_latest.json`。
- `http://127.0.0.1:8765/api/health` 可用于快速查看当前服务是否就绪；响应只包含状态，不返回 API Key 或密码。
