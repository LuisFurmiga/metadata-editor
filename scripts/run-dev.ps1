$Root = Split-Path -Parent $PSScriptRoot
$backend = Start-Process python -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000" -WorkingDirectory "$Root\backend" -PassThru
try { Set-Location "$Root\frontend"; npm run dev } finally { Stop-Process -Id $backend.Id -ErrorAction SilentlyContinue }
