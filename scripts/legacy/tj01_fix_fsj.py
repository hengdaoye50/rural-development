import io
import os
import re

p = os.path.join(os.environ["TEMP"], "tj01", "txt", "tj_2026_fengshoujie_fabuhui.md")
t = io.open(p, encoding="utf-8").read()
i = t.find("9月15日上午，市政府新闻办举行")
t = t[i:] if i > 0 else t
head = "# 2026年天津市中国农民丰收节新闻发布会\n\n"
t = head + t.strip() + "\n"
t = re.sub(r"\n{3,}", "\n\n", t)
io.open(p, "w", encoding="utf-8", newline="\n").write(t)
print(len(t))
print(t[:260])
