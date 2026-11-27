# Fixed offline System.Speech recognition adapter. No generated scripts or grammar commands.
param([Parameter(Mandatory=$true)][string]$Folder)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$data = Get-Content -LiteralPath (Join-Path $Folder 'request.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($data.culture -isnot [string] -or $data.culture -notmatch '^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{2,8}){1,3}$') { throw 'Invalid recognizer culture' }
$installed = @([System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() | Where-Object { $_.Culture.Name -ieq $data.culture })
if ($installed.Count -ne 1) { throw 'Exact culture has no unique installed desktop recognizer' }
$engine = [System.Speech.Recognition.SpeechRecognitionEngine]::new($installed[0])
try {
    $engine.LoadGrammar([System.Speech.Recognition.DictationGrammar]::new())
    $engine.SetInputToWaveFile((Join-Path $Folder 'input.wav'))
    $rows = New-Object 'System.Collections.Generic.List[object]'
    $total = 0
    for ($i=0; $i -lt 129; $i++) {
        $r = $engine.Recognize([TimeSpan]::FromSeconds(5))
        if ($null -eq $r) { break }
        if ($null -eq $r.Audio -or [string]::IsNullOrWhiteSpace($r.Text)) { continue }
        $total += $r.Text.Length
        if ($rows.Count -ge 128 -or $r.Text.Length -gt 4000 -or $total -gt 16000) { throw 'Recognition result exceeds bound' }
        $rows.Add([ordered]@{ text=$r.Text; confidence=[double]$r.Confidence; start_seconds=$r.Audio.AudioPosition.TotalSeconds; duration_seconds=$r.Audio.Duration.TotalSeconds })
    }
    $result = @{ culture=$installed[0].Culture.Name; recognizer_id=$installed[0].Id; segments=$rows.ToArray() }
    $json = ConvertTo-Json -InputObject $result -Depth 5 -Compress
    [System.IO.File]::WriteAllText((Join-Path $Folder 'result.json'),$json,(New-Object System.Text.UTF8Encoding($false)))
} finally {
    $engine.Dispose()
}
