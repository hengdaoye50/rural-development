# -*- coding: utf-8 -*-
"""在「当前前台窗口」输入检索词并回车，然后截图（安全版：前台不是微信就什么都不做）。

设计原则（2026-11-21 事故后）：
  1. **绝不**调用 ShowWindow / SetForegroundWindow —— 微信 4.x 是隐藏的 Qt 窗口，
     调不动，反而会把按键发到别的程序里；
  2. 先检查前台窗口的进程是否为 Weixin.exe，不是就退出，不碰剪贴板、不发按键；
  3. 中文走剪贴板 + Ctrl+V（pywinauto 直接发中文不可靠）；
  4. 回车后等 2.5s 截图，供判读结果。

用法：
  python scripts/_wx_type.py "第五批省级乡村振兴片区" [--shot 路径] [--no-enter]
"""
from __future__ import annotations

import argparse
import ctypes
import sys
import time

import psutil
import win32clipboard
import win32con
import win32gui
import win32process
from PIL import ImageGrab
from pywinauto.keyboard import send_keys

sys.stdout.reconfigure(encoding="utf-8")


def foreground_info():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        exe = psutil.Process(pid).name()
    except Exception:  # noqa: BLE001
        exe = "?"
    return hwnd, exe, win32gui.GetWindowText(hwnd), win32gui.GetClassName(hwnd)


def copy_text(s: str) -> None:
    for _ in range(5):
        try:
            win32clipboard.OpenClipboard()
            break
        except Exception:  # noqa: BLE001
            time.sleep(0.2)
    else:
        raise RuntimeError("剪贴板被占用")
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, s)
    finally:
        win32clipboard.CloseClipboard()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--shot", default=r"data\stage\candidates\_wx_shot.png")
    ap.add_argument("--no-enter", action="store_true")
    args = ap.parse_args()

    hwnd, exe, title, cls = foreground_info()
    print(f"前台：{exe}｜{title[:30]}｜{cls}")
    if exe.lower() not in ("weixin.exe", "wechat.exe"):
        print("✗ 前台不是微信，未发送任何按键 / 未改剪贴板。请先把微信搜索框点开再叫我。")
        return 2

    copy_text(args.query)
    time.sleep(0.3)
    send_keys("^v")
    time.sleep(0.8)
    if not args.no_enter:
        send_keys("{ENTER}")
        time.sleep(2.5)
    img = ImageGrab.grab()
    img.save(args.shot)
    print("✓ 已输入并截图：", args.shot, img.size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
