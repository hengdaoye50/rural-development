# 抓取「杭州市片区资源清单」系列文章正文（经 opencli 浏览器桥渲染）
# 用法：. .\scripts\fetch_hz_lists.ps1
$js = "$env:USERPROFILE\scoop\apps\nodejs-lts\current\bin\node_modules\@jackwener\opencli\dist\src\main.js"
$outDir = Join-Path $PWD "data\raw\ZJ\2026-hz-resource-lists"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$items = @(
  @{ k = "yuhang";   u = "http://mp.weixin.qq.com/s?__biz=MzA5ODc5MjIzMQ==&mid=2650154507&idx=3&sn=fe014a29e71d776dc999c3f1371d81a2" },
  @{ k = "qiantang"; u = "http://mp.weixin.qq.com/s?__biz=MzA5ODc5MjIzMQ==&mid=2650156448&idx=3&sn=d25bf64853370769198339228a95a13f" },
  @{ k = "fuyang";   u = "http://mp.weixin.qq.com/s?__biz=MzA5ODc5MjIzMQ==&mid=2650157746&idx=3&sn=1c664ca6baa1ddcb4bd326a4118b7c52" },
  @{ k = "chunan";   u = "http://mp.weixin.qq.com/s?__biz=MjM5MDMyNzQ1MA==&mid=2650530474&idx=3&sn=94437c9b404a9b56ac9086cf00e4ff55" },
  @{ k = "linping";  u = "http://mp.weixin.qq.com/s?__biz=Mzg5OTYxNTE1MQ==&mid=2247613610&idx=1&sn=8d6caf060b67fe5c03466ab88de333fe" },
  @{ k = "tonglu";   u = "https://m.sohu.com/a/1035352717_121106994" },
  @{ k = "jiande";   u = "https://www.sohu.com/a/1038080877_121106994" },
  @{ k = "xihu";     u = "https://m.sohu.com/a/1030647584_121106994" }
)

foreach ($it in $items) {
  $dest = Join-Path $outDir ("{0}.md" -f $it.k)
  if (Test-Path $dest) { Write-Host "skip $($it.k)"; continue }
  node $js browser main open $it.u 2>$null | Out-Null
  Start-Sleep -Seconds 7
  $lines = node $js browser main eval "document.body.innerText" 2>$null
  $txt = ($lines -join "`n")
  if (-not $txt -or $txt.Length -lt 200) { Write-Host ("FAIL {0}: {1} chars" -f $it.k, $txt.Length); continue }
  [IO.File]::WriteAllText($dest, $txt, [Text.UTF8Encoding]::new($false))
  Write-Host ("ok {0} ({1} chars)" -f $it.k, $txt.Length)
}
