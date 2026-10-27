param([Parameter(Mandatory = $true)][string]$Presentacion)
$ErrorActionPreference = 'Stop'
$taskPath = (Resolve-Path -LiteralPath $Presentacion).Path
$taskParent = [System.IO.Path]::GetDirectoryName($taskPath)
$taskTemporary = Join-Path $taskParent ('normalizada_' + [System.Guid]::NewGuid().ToString('N') + '.pptx')
$taskApp = $null
$taskDeck = $null
try {
    $taskApp = New-Object -ComObject PowerPoint.Application
    # Reescritura nativa del paquete OOXML; conserva tablas y textos editables.
    $taskDeck = $taskApp.Presentations.Open2007($taskPath, -1, 0, 0, -1)
    $taskDeck.SaveCopyAs($taskTemporary, 24)
    $taskDeck.Close()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($taskDeck)
    $taskDeck = $null
    Move-Item -LiteralPath $taskTemporary -Destination $taskPath -Force
    Write-Output $taskPath
} finally {
    if ($null -ne $taskDeck) { $taskDeck.Close(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($taskDeck) }
    if ($null -ne $taskApp) { $taskApp.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($taskApp) }
    if (Test-Path -LiteralPath $taskTemporary) { Remove-Item -LiteralPath $taskTemporary }
}
