AIeyu 服务器上传包

1. 将整个 AIeyu 文件夹解压或覆盖到服务器，例如 C:\AIeyu。
2. 将服务器原有的 .env 放回 C:\AIeyu\.env。压缩包不包含 API Key。
3. 如果服务器已有学生账号和学习记录，请先备份并保留服务器原有 database\russian_ai_tutor.sqlite；如果是首次部署，包内数据库已经包含最新 TEM4/TEM8 题库和词库。
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
- 如果需要使用本包最新数据库，确认已备份服务器旧数据库后，再用包内数据库覆盖。

本包不包含：.env、.git、.venv、原始 PDF、处理过程备份和本地缓存。
