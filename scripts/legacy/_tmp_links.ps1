param(
    [Parameter(Mandatory=$true)][string]$Url,
    [string]$Pattern = '乡村振兴|示范带|片区|xczx|zdly|zcwj|zcfg|zfgb|tzgg|gkml'
)
$ErrorActionPreference = 'Stop'
$h = @{
    'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    'Accept' = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    'Accept-Language' = 'zh-CN,zh;q=0.9'
}
try {
    $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 30 -Headers $h
} catch {
    Write-Output "FETCHERR $Url : $($_.Exception.Message)"
    exit
}
$bytes = $r.RawContentStream.ToArray()
$probe = [System.Text.Encoding]::UTF8.GetString($bytes, 0, [Math]::Min(2000, $bytes.Length))
if ($probe -match 'charset=["'']?gb') { $enc = [System.Text.Encoding]::GetEncoding('GB18030') } else { $enc = [System.Text.Encoding]::UTF8 }
$html = $enc.GetString($bytes)
Write-Output "OK $Url len=$($html.Length)"
$ms = [regex]::Matches($html, '(?is)<a[^>]*href=["'']([^"'']+)["''][^>]*>(.*?)</a>')
$seen = @{}
foreach ($m in $ms) {
    $href = $m.Groups[1].Value
    $text = ([regex]::Replace($m.Groups[2].Value, '(?s)<[^>]+>', '')).Trim()
    if (-not $text) { continue }
    if ($text -notmatch $Pattern -and $href -notmatch $Pattern) { continue }
    $key = "$href"
    if ($seen.ContainsKey($key)) { continue }
    $seen[$key] = 1
    Write-Output ("  {0}  <<  {1}" -f $text, $href)
}
