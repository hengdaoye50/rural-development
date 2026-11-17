import sys
import _tmp_fetch as f

CAND = {
    "衡山县": ["www.hengshan.gov.cn", "www.hsx.gov.cn"],
    "岳阳县": ["www.yyx.gov.cn", "www.yueyangxian.gov.cn"],
    "汉寿县": ["www.hanshou.gov.cn"],
    "澧县": ["www.lixian.gov.cn"],
    "津市市": ["www.jinshi.gov.cn"],
    "赫山区": ["www.heshan.gov.cn"],
    "汨罗市": ["www.miluo.gov.cn"],
    "武陵区": ["www.wuling.gov.cn"],
    "临澧县": ["www.linli.gov.cn", "www.linan.gov.cn"],
}

PATHS = ["/qzf/gzbg/", "/zfxxgk/gzbg/", "/zwgk/gzbg/"]

if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for name, hosts in CAND.items():
        if only and only != name:
            continue
        for host in hosts:
            for p in PATHS:
                url = "http://" + host + p
                try:
                    h = f.fetch(url, timeout=12)
                    print("OK  ", name, url, "len", len(h))
                    break
                except Exception as e:
                    print("FAIL", name, url, type(e).__name__, str(e)[:60])
