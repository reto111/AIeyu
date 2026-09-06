AIeyu 已有服务器更新包

本次更新请优先阅读 UPDATE_README.md。本包不含数据库，不用于首次空库部署。

1. 将整个 AIeyu 文件夹解压或覆盖到服务器，例如 C:\AIeyu。
2. 保留服务器原有 C:\AIeyu\.env。压缩包不包含 API Key。
3. 先备份并保留服务器原有 database\russian_ai_tutor.sqlite。本包不包含数据库，不会更新题库或学生记录；首次部署需另行准备初始数据库。
4. 在 PowerShell 中执行：

   cd C:\AIeyu
   python .\scripts\serve_student_app.py --host 0.0.0.0 --port 8765

5. 或使用启动脚本：

   powershell -ExecutionPolicy Bypass -File .\Start_AIeyu_Server.ps1 -Port 8765

6. 阿里云安全组和 Windows 防火墙都需要开放 TCP 8765。
7. 浏览器访问：http://服务器公网IP:8765/

更新已有服务器时：
- 先停止旧 Python 服务。
- 备份服务器的 database\russian_ai_tutor.sqlite。
- 覆盖代码文件时保留服务器 .env 和服务器数据库，以保留账号、错题和学习记录。
- 已有学生数据时不要用包内数据库覆盖。内容更新使用本次发布指定的补丁；2026-09-03 多模态修正先运行 python -B scripts\content_patch.py 预览，冲突为空才加 --apply 执行。完整步骤及回滚条件见 docs\content_update_workflow.md。

本包不包含：.env、.git、.venv、原始 PDF、处理过程备份和本地缓存。
