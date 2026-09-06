# AIeyu 2026-09-06 服务器更新

本包用于已有 AIeyu 服务器。包含最新学生端视觉、俄语标识、全局提建议窗口及配套代码。不是首次部署包。

## 保留文件

不要删除服务器文件夹，不要替换学生数据库。本包不包含以下文件，请保留服务器现有文件：

- `C:\AIeyu\.env`
- `C:\AIeyu\database\russian_ai_tutor.sqlite`

本次没有新增题库内容，不需要运行历史题库/词库导入、修复脚本，也不需要运行 content_patch.py。

## 更新步骤

1. 在正在运行旧服务的终端按 Ctrl+C 停止服务。如果是后台服务，先按原有方式停止，避免新旧进程同时运行。
2. 在 PowerShell 备份数据库：

```powershell
cd C:\AIeyu
Copy-Item .\database\russian_ai_tutor.sqlite (".\database\russian_ai_tutor_backup_" + (Get-Date -Format 'yyyyMMdd_HHmmss') + ".sqlite")
```

3. 将 ZIP 内的文件解压覆盖到 `C:\AIeyu`。ZIP 根目录直接是 apps、scripts 等目录，不要多套一层 AIeyu 文件夹。确认 `C:\AIeyu\apps\student_web\static\student-refinement.css` 存在。
4. 在 PowerShell 启动：

```powershell
cd C:\AIeyu
python .\scripts\serve_student_app.py --host 0.0.0.0 --port 8765
```

保留这个服务窗口。如果缺少俄语词形依赖，再执行 `python -m pip install -r requirements-web.txt` 后重新启动。使用原来正常运行服务的 Python 环境。

5. 在浏览器按 Ctrl+F5 强制刷新；手机重新加载页面。检查顶部的“提建议”、俄语标识，以及自己的学习记录仍在。

另开 PowerShell 窗口可检查健康状态：

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/health
```

需要检查完整业务时使用 `python -B scripts\check_mvp_readiness.py --base-url http://127.0.0.1:8765`。出现题库数量、质量等旧数据问题时保留报告，不要用本地数据库覆盖服务器。

## 范围说明

包内不包含 .env、SQLite 数据库、原始 PDF、本地依赖环境、缓存和学生个人数据。代码包包含历史工具，但不会自动执行。此次打包不代表已经部署或验证过服务器。
