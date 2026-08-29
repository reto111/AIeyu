param(
  [int]$Port = 8765
)

Set-Location -Path $PSScriptRoot
python scripts\serve_student_app.py --host 0.0.0.0 --port $Port
