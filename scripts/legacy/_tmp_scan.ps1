param(
    [Parameter(Mandatory=$true)][string[]]$Urls,
    [int]$Pages = 6,
    [string]$Pattern = '示范带|片区|乡村振兴'
)
$ErrorActionPreference = 'Continue'
$h = @{
    'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    'Accept-Language' = 'zh-CN,zh;q=0.9'
}
function Get-Html([string]$u) {
    try {
        $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 25 -Headers $h
    } catch { return $null }
    $bytes = $r.RawContentStream.ToArray()
    $probe = [System.Text.Encoding]::UTF8.GetString($bytes, 0, [Math]::Min(1500, $bytes.Length))
    if ($probe -match 'charset=["'']?gb') { $enc = [System.Text.Encoding]::GetEncoding('GB18030') } else { $enc = [System.Text.Encoding]::UTF8 }
    return $enc.GetString($bytes)
}
foreach ($base in $Urls) {
    Write-Output "########## $base"
    for ($p = 1; $p -le $Pages; $p++) {
        if ($p -eq 1) { $u = $base } else {
            if ($base -match 'index\.html$') { $u = $base -replace 'index\.html$', "index_$p.html" } else { break }
        }
        $html = Get-Html $u
        if (-not $html) { Write-Output "  [fail page $p] $u"; continue }
        $ms = [regex]::Matches($html, '(?is)<a[^>]*href=["'']([^"'']+)["''][^>]*>(.*?)</a>')
        foreach ($m in $ms) {
            $text = ([regex]::Replace($m.Groups[2].Value, '(?s)<[^>]+>', '')).Trim()
            if ($text.Length -lt 6) { continue }
            if ($text -notmatch $Pattern) { continue }
            Write-Output ("  p{0} {1}  <<  {2}" -f $p, $text, $m.Groups[1].Value)
        }
    }
}
