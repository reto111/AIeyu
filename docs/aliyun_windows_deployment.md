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

学生端本地服务目前只依赖 Python 标准库，部署网页原型不需要安装复杂后端依赖。

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
