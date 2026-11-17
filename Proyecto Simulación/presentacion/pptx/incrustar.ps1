param([string]$entrada, [string]$salida)
# Abre el .pptx en PowerPoint y lo guarda con las fuentes incrustadas (Guardar como > Incrustar fuentes).
$yaAbierto = Get-Process POWERPNT -ErrorAction SilentlyContinue
$app = New-Object -ComObject PowerPoint.Application
try {
  $pres = $app.Presentations.Open($entrada, $false, $false, $false)
  if (Test-Path $salida) { Remove-Item $salida -Force }
  $pres.SaveAs($salida, 24, -1)   # 24 = ppSaveAsOpenXMLPresentation, -1 = msoTrue (incrustar TrueType)
  $pres.Close()
} finally {
  if (-not $yaAbierto) { $app.Quit() }
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($salida)
$zip.Entries | Where-Object { $_.FullName -like "ppt/fonts/*" } | ForEach-Object { "{0}  {1:N0} bytes" -f $_.FullName, $_.Length }
$zip.Dispose()
"tamaño total: {0:N0} bytes" -f (Get-Item $salida).Length
