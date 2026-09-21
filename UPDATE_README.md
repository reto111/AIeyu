# AIeyu 2026-09-21 服务器更新

适用于已有 Windows 服务器，不是首次部署包。包含最新界面、AI 等待转圈、统一分级背词、注册年级选择、6587 条审核标注及 20 条伪来源归档。412 条仍待标注；题库使用服务器现有数据。

## 1. 停止与备份

在旧服务窗口按 Ctrl+C。若由后台服务管理，请停止对应服务，不要结束所有 Python 进程。管理员 PowerShell：

```powershell
cd C:\AIeyu
$backup = "C:\AIeyu_backup_" + (Get-Date -Format 'yyyyMMdd_HHmmss')
Copy-Item -LiteralPath C:\AIeyu -Destination $backup -Recurse
Write-Host "备份位置：$backup"
```

确认成功再覆盖。备份含密钥和学生资料，仅留服务器，不要公开。

## 2. 解压覆盖

上传 ZIP，解压到 `C:\AIeyu`，覆盖同名代码。ZIP 根目录直接有 apps、scripts 等，不要套第二层目录。**不要先删除原项目。**

本包不含 `.env`、SQLite 数据库、原始 PDF 或学生数据。保留 `C:\AIeyu\.env` 和 `C:\AIeyu\database\russian_ai_tutor.sqlite`；旁边若有 `-wal`、`-shm` 文件也不要手工删除。

## 3. 预检并导入审核标注

使用原来运行服务的 Python 环境：

```powershell
cd C:\AIeyu
python -m pip install -r .\requirements-web.txt
python -X utf8 -B .\scripts\update_release.py
```

预检在数据库副本上执行全部标注与归档，并比较其他业务表。看到 `validated: true` 后执行：

```powershell
python -X utf8 -B .\scripts\update_release.py --apply
```

按稳定来源键和原值匹配，不依赖服务器 ID 与本机一致。若出现来源缺失、原值变化或已有不同审核内容，停止更新并把完整报错发回；不要强制覆盖、替换数据库或重放历史批次。可恢复备份运行旧版。137旧草稿不能重放。

## 4. 启动与检查

```powershell
cd C:\AIeyu
python -X utf8 -B .\scripts\serve_student_app.py --host 0.0.0.0 --port 8765
```

保留窗口。另开 PowerShell：

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/health
```

浏览器 Ctrl+F5，手机重新加载。检查原账号和学习记录、三种词库、重音及体对、AI 等待和提建议窗口。真实 AI 请求使用服务器原密钥，可能产生原有服务商费用。端口和安全组不用更改。

## 5. 回退

停止新服务，将步骤1完整备份恢复到项目位置，保持代码和数据库为同一版本。不要只恢复其中一项；新版本目录先保留备用。备份后的新作答不会在旧备份中，恢复前确认是否已有学生使用新版。

本包已本地验证，不代表已经部署或验证服务器。
