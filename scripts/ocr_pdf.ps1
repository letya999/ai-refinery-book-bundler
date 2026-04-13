param([string]$ImagePath)

Add-Type -AssemblyName System.Runtime.WindowsRuntime

function Await($task) {
    $awaiter = $task.GetAwaiter()
    while (-not $awaiter.IsCompleted) { Start-Sleep -Milliseconds 50 }
    $awaiter.GetResult()
}

[void][Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime]
[void][Windows.Storage.StorageFile, Windows.Foundation, ContentType=WindowsRuntime]
[void][Windows.Media.Imaging.BitmapDecoder, Windows.Foundation, ContentType=WindowsRuntime]
[void][Windows.Graphics.Imaging.SoftwareBitmap, Windows.Foundation, ContentType=WindowsRuntime]

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage(
    [Windows.Globalization.Language]::new("ru")
)

$file = Await([Windows.Storage.StorageFile]::GetFileFromPathAsync($ImagePath))
$stream = Await($file.OpenAsync([Windows.Storage.FileAccessMode]::Read))
$decoder = Await([Windows.Media.Imaging.BitmapDecoder]::CreateAsync($stream))
$bitmap = Await($decoder.GetSoftwareBitmapAsync())
$result = Await($engine.RecognizeAsync($bitmap))

Write-Output $result.Text
