$binPath = "C:\xampp\mysql\bin\mysqld.exe"
if (Test-Path $binPath) {
    Write-Host "Old MySQL binary found: $binPath"
    try {
        $versionInfo = & $binPath --version
        Write-Host "Old MySQL Version: $versionInfo"
    } catch {
        Write-Host "Failed to get version: $_"
    }
} else {
    Write-Host "Old MySQL binary NOT found."
}
