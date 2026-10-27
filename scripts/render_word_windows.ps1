param(
    [Parameter(Mandatory = $true)][string]$Documento,
    [Parameter(Mandatory = $true)][string]$Salida
)
$ErrorActionPreference = 'Stop'
# Exportación nativa de Word para comprobar el diseño del DOCX en Windows.
$taskDocPath = (Resolve-Path -LiteralPath $Documento).Path
$taskPdfPath = [System.IO.Path]::GetFullPath($Salida)
[void][System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($taskPdfPath))
$taskWordApp = $null
$taskWordDoc = $null
try {
    $taskWordApp = New-Object -ComObject Word.Application
    $taskWordApp.Visible = $false
    $taskWordApp.DisplayAlerts = 0
    $taskWordDoc = $taskWordApp.Documents.Open($taskDocPath, $false, $true)
    $taskWordDoc.Repaginate()
    $taskWordDoc.ExportAsFixedFormat($taskPdfPath, 17)
    Write-Output $taskPdfPath
} finally {
    if ($null -ne $taskWordDoc) { $taskWordDoc.Close($false); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($taskWordDoc) }
    if ($null -ne $taskWordApp) { $taskWordApp.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($taskWordApp) }
}
