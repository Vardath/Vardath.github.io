# Fixed offline PNG/JPEG normalizer. Never evaluates image metadata as code.
param([Parameter(Mandatory=$true)][string]$Folder)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$image=[System.Drawing.Image]::FromFile((Join-Path $Folder 'input.image'))
try {
    if ($image.RawFormat.Guid -ne [System.Drawing.Imaging.ImageFormat]::Png.Guid -and
        $image.RawFormat.Guid -ne [System.Drawing.Imaging.ImageFormat]::Jpeg.Guid) { throw 'Only PNG and JPEG are supported' }
    if ($image.Width -lt 1 -or $image.Height -lt 1 -or $image.Width -gt 8192 -or $image.Height -gt 8192 -or
        ([long]$image.Width * $image.Height) -gt 24000000) { throw 'Image dimensions exceed decode bound' }
    $scale=[Math]::Min(1.0,1920.0/[Math]::Max($image.Width,$image.Height))
    $w=[Math]::Max(1,[int][Math]::Round($image.Width*$scale))
    $h=[Math]::Max(1,[int][Math]::Round($image.Height*$scale))
    $bitmap=New-Object System.Drawing.Bitmap($w,$h,[System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
    try {
        $g=[System.Drawing.Graphics]::FromImage($bitmap)
        try {
            $g.Clear([System.Drawing.Color]::Black)
            $g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $g.DrawImage($image,0,0,$w,$h)
        } finally {$g.Dispose()}
        $bitmap.Save((Join-Path $Folder 'image.png'),[System.Drawing.Imaging.ImageFormat]::Png)
    } finally {$bitmap.Dispose()}
} finally {$image.Dispose()}
