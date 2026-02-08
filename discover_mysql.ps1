$serviceName = "MySQL80"
$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "Service '$serviceName' found. Status: $($service.Status)"
    $wmi = Get-CimInstance win32_service | Where-Object {$_.Name -eq $serviceName}
    $path = $wmi.PathName
    Write-Host "Service Binary Path: $path"

    $programData = $env:ProgramData
    $iniPath = "$programData\MySQL\MySQL Server 8.0\my.ini"
    
    if (Test-Path $iniPath) {
        Write-Host "Found my.ini at $iniPath"
        $datadirLine = Select-String -Path $iniPath -Pattern "datadir="
        Write-Host "Configured DataDir: $datadirLine"
    } else {
        Write-Host "Could not find standard my.ini at $iniPath"
    }
} else {
    Write-Host "Service '$serviceName' not found."
}

$sourcePath = "C:\xampp\mysql\data"
if (Test-Path $sourcePath) {
    Write-Host "Source directory exists: $sourcePath"
    if (Test-Path "$sourcePath\puretego_crm") {
        Write-Host "Database folder 'puretego_crm' found."
    } else {
        Write-Host "Database folder 'puretego_crm' NOT found."
    }
    
    if (Test-Path "$sourcePath\ibdata1") {
        Write-Host "ibdata1 found."
    }
} else {
    Write-Host "Source directory NOT found: $sourcePath"
}
