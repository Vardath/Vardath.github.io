# Fixed local Windows speech adapter. Narration is data, never PowerShell code or SSML.
param([Parameter(Mandatory=$true)][ValidateSet('voices','speak')][string]$Mode,
      [Parameter(Mandatory=$true)][string]$Folder)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $voices = @($synth.GetInstalledVoices() | Where-Object { $_.Enabled } | ForEach-Object {
        $v = $_.VoiceInfo
        [ordered]@{ id=$v.Id; name=$v.Name; culture=$v.Culture.Name; gender=$v.Gender.ToString() }
    })
    if ($Mode -eq 'voices') {
        $result = @{ voices=$voices }
    } else {
        $data = Get-Content -LiteralPath (Join-Path $Folder 'request.json') -Raw -Encoding UTF8 | ConvertFrom-Json
        $chosen = @($voices | Where-Object { $_.id -ceq $data.voice.id -and $_.name -ceq $data.voice.name -and $_.culture -ceq $data.voice.culture })
        if ($chosen.Count -ne 1) { throw 'Selected installed voice changed or is unavailable' }
        if ($data.text -isnot [string] -or $data.text.Length -lt 1 -or $data.text.Length -gt 2000) { throw 'Invalid narration text' }
        $synth.SelectVoice($chosen[0].name)
        if ($synth.Voice.Id -cne $chosen[0].id) { throw 'Speech engine selected another voice' }
        $synth.Rate = 0
        $synth.Volume = 100
        $format = [System.Speech.AudioFormat.SpeechAudioFormatInfo]::new(22050,[System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,[System.Speech.AudioFormat.AudioChannel]::Mono)
        $synth.SetOutputToWaveFile((Join-Path $Folder 'speech.wav'),$format)
        $synth.Speak([string]$data.text)
        $synth.SetOutputToNull()
        $result = @{ voice=$chosen[0] }
    }
    $json = ConvertTo-Json -InputObject $result -Depth 5 -Compress
    [System.IO.File]::WriteAllText((Join-Path $Folder 'result.json'),$json,(New-Object System.Text.UTF8Encoding($false)))
} finally {
    $synth.Dispose()
}
