# Render every slide of a .pptx to PNG with the installed PowerPoint (true fonts, true layout).
#   powershell -NoProfile -ExecutionPolicy Bypass -File render.ps1 deck.pptx outdir [width] [height] [pdf]
param(
  [Parameter(Mandatory = $true)][string]$Pptx,
  [Parameter(Mandatory = $true)][string]$OutDir,
  [int]$Width = 1920,
  [int]$Height = 1080,
  [string]$Pdf = ''
)
$ErrorActionPreference = 'Stop'
$Pptx = (Resolve-Path $Pptx).Path
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$OutDir = (Resolve-Path $OutDir).Path
Get-ChildItem $OutDir -Filter 'slide-*.png' | Remove-Item -Force

$app = New-Object -ComObject PowerPoint.Application
try {
  # ReadOnly = msoTrue, Untitled = msoFalse, WithWindow = msoFalse
  $pres = $app.Presentations.Open($Pptx, -1, 0, 0)
  try {
    foreach ($s in $pres.Slides) {
      $file = Join-Path $OutDir ('slide-{0:D2}.png' -f $s.SlideIndex)
      $s.Export($file, 'PNG', $Width, $Height)
      Write-Output $file
    }
    if ($Pdf -ne '') {
      $pres.SaveCopyAs($Pdf, 32)   # ppSaveAsPDF
      Write-Output $Pdf
    }
  } finally { $pres.Close() }
} finally {
  # PowerPoint is single-instance: never quit a session the user has documents open in
  if ($app.Presentations.Count -eq 0) { $app.Quit() }
  [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
