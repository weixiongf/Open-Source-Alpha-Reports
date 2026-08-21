# -*- coding: utf-8 -*-
"""make_cover.py — 生成 README 首屏 banner（开源掘金报告主题封面）。

纯 PIL 绘制：深色 GitHub 暗色调 + 金色矿脉/数据流装饰 + 思源黑体排版。
输出: github_reports_repo/assets/cover.png (1792x1024)
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = ROOT / "assets" / "fonts" / "SourceHanSansCN" / "SubsetOTF" / "CN"
OUT = Path(__file__).resolve().parents[1] / "assets" / "cover.png"

W, H = 1792, 1024

# ---- 配色（GitHub 暗色 + 掘金金） ----
BG_TOP = (13, 17, 23)        # #0D1117
BG_BOTTOM = (26, 32, 44)     # #161B22 略亮
GOLD_BRIGHT = (248, 213, 126)
GOLD = (227, 179, 65)
GOLD_DEEP = (192, 138, 30)
TEXT_WHITE = (230, 237, 243)
TEXT_GRAY = (201, 209, 217)
TEXT_DIM = (139, 148, 158)
BLUE = (88, 166, 255)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def lerp(a, b, t):
    return int(a + (b - a) * t)


def lerp_color(c1, c2, t):
    return tuple(lerp(c1[i], c2[i], t) for i in range(3))


def gradient_text(img, xy, text, fnt, stops):
    """按 stops 垂直渐变渲染文字（stops: [(t, (r,g,b)), ...]）。"""
    probe = ImageDraw.Draw(img)
    bbox = probe.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 8
    mask = Image.new("L", (tw + pad * 2, th + pad * 2), 0)
    ImageDraw.Draw(mask).text((pad - bbox[0], pad - bbox[1]), text, font=fnt, fill=255)

    grad = Image.new("RGBA", mask.size)
    gpx = grad.load()
    for y in range(grad.size[1]):
        t = y / max(1, grad.size[1] - 1)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                tt = (t - t0) / max(1e-6, t1 - t0)
                col = lerp_color(c0, c1, tt)
                break
        else:
            col = stops[-1][1]
        for x in range(grad.size[0]):
            a = mask.getpixel((x, y))
            if a:
                gpx[x, y] = (*col, a)
    img.paste(grad, (xy[0] - pad + bbox[0], xy[1] - pad + bbox[1]), grad)


def spaced_text(draw, xy, text, fnt, fill, gap=0):
    """逐字符绘制（模拟 letter-spacing），返回总宽度。"""
    x, y = xy
    total = 0
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        w = draw.textlength(ch, font=fnt)
        x += w + gap
        total += w + gap
    return total


def main() -> None:
    random.seed(20260821)
    img = Image.new("RGB", (W, H), BG_TOP)
    px = img.load()

    # ---- 1. 垂直渐变背景 ----
    for y in range(H):
        t = y / (H - 1)
        col = lerp_color(BG_TOP, BG_BOTTOM, t)
        for x in range(W):
            px[x, y] = col

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    # ---- 2. 网格 ----
    for gx in range(0, W, 96):
        od.line([(gx, 0), (gx, H)], fill=(88, 166, 255, 10), width=1)
    for gy in range(0, H, 96):
        od.line([(0, gy), (W, gy)], fill=(88, 166, 255, 10), width=1)

    # ---- 3. 右上金色光晕 ----
    glow_cx, glow_cy = 1540, 170
    for r, a in ((520, 14), (400, 18), (280, 22), (170, 26), (90, 30)):
        od.ellipse([glow_cx - r, glow_cy - r, glow_cx + r, glow_cy + r],
                   fill=(227, 179, 65, a))

    # ---- 4. 金色矿脉折线（左下 → 右上），多层模拟发光 ----
    pts = []
    x = -60
    y = H + 120
    pts.append((x, y))
    while x < W + 80:
        x += random.randint(150, 260)
        y -= random.randint(70, 150)
        pts.append((x, max(40, y)))
    for width, alpha in ((14, 26), (7, 55), (3, 110), (1, 190)):
        od.line(pts, fill=(227, 179, 65, alpha), width=width,
                joint="curve")

    # 矿脉上的金色粒子
    for p in pts:
        for _ in range(5):
            jx = p[0] + random.randint(-70, 70)
            jy = p[1] + random.randint(-70, 70)
            r = random.choice([2, 3, 4, 5])
            od.ellipse([jx - r, jy - r, jx + r, jy + r],
                       fill=(248, 213, 126, random.randint(40, 150)))
    # 散落粒子
    for _ in range(60):
        jx = random.randint(0, W)
        jy = random.randint(0, H)
        r = random.choice([1, 2, 3])
        od.ellipse([jx - r, jy - r, jx + r, jy + r],
                   fill=(227, 179, 65, random.randint(18, 80)))

    img = Image.alpha_composite(img.convert("RGBA"), overlay)

    # 轻微柔化光晕与矿脉
    glow_layer = img.filter(ImageFilter.GaussianBlur(1.2))
    img = Image.blend(img, glow_layer, 0.18).convert("RGB")

    draw = ImageDraw.Draw(img)
    M = 120  # 左边距

    # ---- 5. 顶部英文小标 ----
    spaced_text(draw, (M, 96), "OPEN-SOURCE ALPHA REPORTS",
                font("SourceHanSansCN-Medium.otf", 34), GOLD_DEEP, gap=6)

    # ---- 6. 主标题（金色渐变） ----
    f_title = font("SourceHanSansCN-Heavy.otf", 152)
    gradient_text(img, (M, 140), "开源掘金报告", f_title, [
        (0.0, GOLD_BRIGHT), (0.55, GOLD), (1.0, GOLD_DEEP),
    ])

    # ---- 7. 副标题 ----
    f_sub = font("SourceHanSansCN-Regular.otf", 44)
    draw.text((M, 370), "以「商业价值」为第一视角的 GitHub 开源项目深度分析档案库",
              font=f_sub, fill=TEXT_GRAY)

    # ---- 8. 三张指标卡 ----
    cards = [
        ("11 维评分体系", "D1–D9 加权评分 + D10/D11 平行维度\n市场 · 技术 · 社区 · 商业 · 竞争 · 法律 · 治理"),
        ("S · A · B · C · D", "五级商业化潜力等级\n短板敏感 · 硬伤必标 · 一票否决"),
        ("4 类价值画像", "明星资产 / 纯商业工具\n公共产品型 / 长尾项目"),
    ]
    card_w, card_h, gap = 500, 210, 40
    total_w = card_w * 3 + gap * 2
    cx0 = (W - total_w) // 2
    cy0 = 540
    f_num = font("SourceHanSansCN-Bold.otf", 52)
    f_card = font("SourceHanSansCN-Regular.otf", 27)
    for i, (big, small) in enumerate(cards):
        x0 = cx0 + i * (card_w + gap)
        rect = [x0, cy0, x0 + card_w, cy0 + card_h]
        od2 = ImageDraw.Draw(img)
        od2.rounded_rectangle(rect, radius=22, fill=(22, 27, 34, 235),
                              outline=(227, 179, 65, 150), width=2)
        # 顶部金色短线
        od2.rounded_rectangle([x0 + 34, cy0 + 34, x0 + 34 + 72, cy0 + 40],
                              radius=3, fill=GOLD)
        draw.text((x0 + 34, cy0 + 62), big, font=f_num, fill=GOLD)
        for j, line in enumerate(small.split("\n")):
            draw.text((x0 + 34, cy0 + 142 + j * 37), line, font=f_card,
                      fill=TEXT_DIM)

    # ---- 9. 数据亮点条 ----
    f_hl = font("SourceHanSansCN-Medium.otf", 34)
    hl = ["48 项评分细则", "完整版 PDF", "每日自动更新", "版本化方法论 v1.3"]
    total = 0
    for s in hl:
        total += draw.textlength(s, font=f_hl) + 90
    hx = (W - total + 90) // 2
    for i, s in enumerate(hl):
        draw.text((hx, 816), s, font=f_hl, fill=TEXT_GRAY)
        hx += draw.textlength(s, font=f_hl)
        if i < len(hl) - 1:
            hx += 90
            draw.ellipse([hx - 40, 832, hx - 32, 840], fill=GOLD)

    # ---- 10. 底部署名 ----
    f_sig = font("SourceHanSansCN-Regular.otf", 30)
    draw.text((M, 916), "@魔法工厂 · @向量之心 · @南山科学家", font=f_sig,
              fill=TEXT_DIM)
    sig_w = draw.textlength("@魔法工厂 · @向量之心 · @南山科学家", font=f_sig)
    draw.text((M + sig_w + 56, 916), "|  www.mova.work", font=f_sig, fill=GOLD)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG")
    print("saved:", OUT)


if __name__ == "__main__":
    main()
