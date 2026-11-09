import io
import re

base = r"C:\Users\zjh22\AppData\Local\Temp\tj01\txt"
raw = io.open(base + r"\dl_plan.md", encoding="utf-8").read().split("\n")

head = """# 东丽区人民政府办公室关于印发东丽区乡村旅游重点片区规划的通知

东丽政办〔2024〕10号

各有关单位：

经区人民政府同意，现将《东丽区乡村旅游重点片区规划》印发给你们，请遵照执行。

东丽区人民政府办公室

2024年12月31日

（此件主动公开）

---

"""
keep = []
skip_toc = True
for ln in raw:
    if "HYPERLINK" in ln or "PAGEREF" in ln:
        continue
    if skip_toc and ln.strip() in ("目  录", "目录"):
        skip_toc = False
        continue
    keep.append(ln)
# drop leftover figure/table number stubs
out = [ln for ln in keep if not re.fullmatch(r"\d{5,}", ln.strip())]
text = head + "\n".join(out).strip() + "\n"
# collapse 3+ blank lines
text = re.sub(r"\n{3,}", "\n\n", text)
with io.open(base + r"\dl_plan_clean.md", "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)
print("chars=", len(text.replace("\n", "")))
print(text[:600])
