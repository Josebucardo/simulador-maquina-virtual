param(
    [Parameter(Mandatory = $true)][string]$Presentacion,
    [Parameter(Mandatory = $true)][string]$Salida
)
$ErrorActionPreference = 'Stop'
$taskPptPath = (Resolve-Path -LiteralPath $Presentacion).Path
$taskOutDir = [System.IO.Path]::GetFullPath($Salida)
[void][System.IO.Directory]::CreateDirectory($taskOutDir)
$taskPptApp = $null
$taskDeck = $null
try {
    $taskPptApp = New-Object -ComObject PowerPoint.Application
    $taskDeck = $taskPptApp.Presentations.Open($taskPptPath, -1, 0, 0)
    foreach ($taskSlide in $taskDeck.Slides) {
        $taskPngPath = Join-Path $taskOutDir ('diapositiva_{0:D2}.png' -f $taskSlide.SlideIndex)
        $taskSlide.Export($taskPngPath, 'PNG', 1600, 900)
    }
    $taskDeck.SaveAs((Join-Path $taskOutDir 'DEFENSA_GRUPO13.pdf'), 32)
    Write-Output ('Diapositivas: ' + $taskDeck.Slides.Count)
    Write-Output $taskOutDir
} finally {
    if ($null -ne $taskDeck) { $taskDeck.Close(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($taskDeck) }
    if ($null -ne $taskPptApp) { $taskPptApp.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($taskPptApp) }
}
