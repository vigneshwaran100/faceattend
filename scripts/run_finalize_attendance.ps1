Set-Location "$PSScriptRoot/.."

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Write-Output "======================================"
Write-Output "Attendance finalization started: $timestamp"
Write-Output "======================================"

uv run python scripts/finalize_attendance.py

$exitCode = $LASTEXITCODE

$completedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

if ($exitCode -eq 0) {
    Write-Output "Attendance finalization completed: $completedAt"
}
else {
    Write-Output "Attendance finalization FAILED: $completedAt"
    exit $exitCode
}