from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing


W, H = 1080, 1920
ROOT = Path.cwd()
OUT_DIR = ROOT / "public" / "daily" / "2026-09-26" / "zad-v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_ROOT = Path("/usr/share/fonts/truetype/noto")\nURDU = FONT_ROOT / "NotoNaskhArabic-Regular.ttf"
URDU_BOLD = FONT_ROOT / "NotoNaskhArabic-Bold.ttf"
ROMAN = FONT_ROOT / "NotoSans-Regular.ttf"
ROMAN_MEDIUM = FONT_ROOT / "NotoSans-Regular.ttf"
ROMAN_BOLD = FONT_ROOT / "NotoSans-Bold.ttf"

CREAM = "#F3EDE2"
PAPER = "#FFFCF6"
PANEL = "#FFFDF8"
GREEN_DARK = "#073D31"
GREEN = "#075E49"
GREEN_LIGHT = "#DCEDE6"
GREEN_PALE = "#EEF6F2"
GOLD = "#C49A4A"
GOLD_DARK = "#9B6A18"
TEXT = "#17221D"
MUTED = "#596B63"
WHITE = "#FFFDF8"

INSTITUTE_LINE_1 = "AL FURQAN INSTITUTE OF ISLAMIC STUDIES,"
INSTITUTE_LINE_2 = "MUZAFFARNAGAR"
INSTITUTE_SITE = "www.alfurqan.co.in"
AUTHOR_SITE = "www.hakeemzaki.com"
PHONE = "+91 80064 82710"
TELEGRAM = "@MAFAMZN"


DEFAULT_PAYLOAD = {
    "date_slug": "2026-09-26",
    "date_urdu": "ہفتہ، 26 ستمبر 2026ء  |  13 ربیع الثانی 1448ھ",
    "date_roman": "Saturday, 26 September 2026  |  13 Rabi al-Thani 1448 Hijri",
    "cards": {
    "urdu_deen": {
        "language": "urdu",
        "section": "دین",
        "label": "قسم سے سودا، برکت نہیں",
        "heading": "اللہ کا نام قیمت بڑھانے کا وسیلہ؟",
        "paragraphs": [
            "دکاندار نے کہا: ’’اللہ کی قسم، مجھے یہی چیز اتنے کی پڑی ہے۔‘‘ گاہک مان گیا؛ منافع ہوا، مگر اللہ کا نام نرخ بڑھانے کا اوزار بن گیا۔ سچی قسم بھی کاروباری عادت بنے تو نامِ الٰہی کی ہیبت گھٹتی ہے؛ جھوٹی ہو تو گناہ الگ۔",
            "رسول اللہ صلی اللہ علیہ وسلم نے فرمایا: ’’قسم سامان بکوا دیتی ہے، مگر برکت مٹا دیتی ہے۔‘‘ (صحیح بخاری: 2087) چیز کی خوبی بتائیے، قیمت صاف رکھیے؛ یقین خریدنے کے لیے قسم نہ بیچیے۔ بیع کی برکت صرف زیادہ رقم نہیں، پاک کمائی اور مطمئن ضمیر بھی ہے۔",
        ],
    },
    "urdu_tibb": {
        "language": "urdu",
        "section": "طب — جوڑ کی فوری علامت",
        "label": "ہر سرخ جوڑ گاؤٹ نہیں",
        "heading": "ایک جوڑ اچانک گرم اور سوجا ہوا",
        "paragraphs": [
            "گھٹنا اچانک گرم، سرخ اور شدید دردناک ہوا؛ پرانی ’’یورک ایسڈ‘‘ رپورٹ دیکھ کر دوا خود شروع کرلی۔ گاؤٹ ایسا دکھ سکتا ہے، مگر جوڑ کا جراثیمی انفیکشن بھی یہی صورت بنا سکتا ہے۔ اس میں تاخیر خطرناک ہے، اور بخار نہ ہونا اسے رد نہیں کرتا۔",
            "ایک جوڑ میں اچانک شدید درد، سوجن یا وزن ڈالنے میں مشکل ہو تو اسی دن معائنہ کرائیں—خصوصاً شوگر، کمزور مدافعت یا مصنوعی جوڑ کی صورت میں۔ مالش یا پرانی دوا سے وقت نہ گزاریں؛ جلد علاج جوڑ کو نقصان سے بچا سکتا ہے۔",
        ],
    },
    "roman_deen": {
        "language": "roman",
        "section": "Deen",
        "label": "Qasam Se Sauda, Barkat Nahin",
        "heading": "Allah Ka Naam Rate Badhane Ka Zariya?",
        "paragraphs": [
            "Dukandar bola: “Allah ki qasam, mujhe yahi cheez itne ki padi.” Grahak maan gaya; munafa hua, magar Allah ka naam rate badhane ka auzar ban gaya. Sachchi qasam ki aadat bhi uski haibat ghatati hai; jhooti ho to gunah alag.",
            "Rasulullah sallallahu alaihi wasallam ne farmaya: “Qasam maal bikwa deti hai, magar barkat mita deti hai.” (Sahih Bukhari: 2087) Khoobi aur price saaf rakhein; qasam se yaqeen na khareedein. Barkat paisa hi nahin, paak kamai aur mutmain zameer bhi hai.",
        ],
    },
    "roman_tibb": {
        "language": "roman",
        "section": "Tibb — Joint Ki Fori Alamat",
        "label": "Har Surkh Joint Gout Nahin",
        "heading": "Ek Joint Achanak Garam Aur Sooja Hua",
        "paragraphs": [
            "Ghutna achanak garam, surkh aur dardnaak hua; “uric acid” report dekh kar dawa shuru kar li. Gout aisa lag sakta hai, magar joint infection bhi. Der khatarnak hai; bukhar na ho tab bhi infection kharij nahin hota.",
            "Ek joint mein achanak shadeed dard, swelling ya weight dalne mein mushkil ho to usi din check-up karayein—khaas kar diabetes, weak immunity ya artificial joint mein. Massage ya purani dawa se waqt na guzarein; jaldi treatment damage se bacha sakta hai.",
        ],
    },
    },
}


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def text_width(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, rtl: bool = False) -> int:
    kwargs = {"direction": "rtl", "language": "ur"} if rtl else {}
    box = draw.textbbox((0, 0), text, font=fnt, **kwargs)
    return box[2] - box[0]


def wrap_words(
    draw: ImageDraw.ImageDraw,
    paragraph: str,
    fnt: ImageFont.FreeTypeFont,
    max_width: int,
    rtl: bool = False,
) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in paragraph.split():
        trial = word if not current else f"{current} {word}"
        if text_width(draw, trial, fnt, rtl) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_rtl_top(
    draw: ImageDraw.ImageDraw,
    text: str,
    right: int,
    top: int,
    fnt: ImageFont.FreeTypeFont,
    fill: str,
) -> None:
    box = draw.textbbox((0, 0), text, font=fnt, direction="rtl", language="ur")
    draw.text(
        (right - box[2], top - box[1]),
        text,
        font=fnt,
        fill=fill,
        direction="rtl",
        language="ur",
    )


def draw_rtl_anchor(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    fnt: ImageFont.FreeTypeFont,
    fill: str,
    anchor: str = "ra",
) -> None:
    draw.text(
        xy,
        text,
        font=fnt,
        fill=fill,
        anchor=anchor,
        direction="rtl",
        language="ur",
    )


def make_qr(size: int = 150) -> Image.Image:
    widget = qr.QrCodeWidget("https://t.me/MAFAMZN")
    x1, y1, x2, y2 = widget.getBounds()
    drawing = Drawing(
        size,
        size,
        transform=[size / (x2 - x1), 0, 0, size / (y2 - y1), 0, 0],
    )
    drawing.add(widget)
    with tempfile.TemporaryDirectory() as td:
        pdf = Path(td) / "qr.pdf"
        prefix = Path(td) / "qr"
        renderPDF.drawToFile(drawing, str(pdf))
        subprocess.run(
            [
                "pdftoppm",
                "-f",
                "1",
                "-singlefile",
                "-png",
                "-r",
                "72",
                str(pdf),
                str(prefix),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        image = Image.open(str(prefix) + ".png").convert("RGB").resize((size, size))

    pix = image.load()
    dark = (7, 61, 49)
    light = (255, 252, 246)
    for y in range(image.height):
        for x in range(image.width):
            r, g, b = pix[x, y]
            pix[x, y] = dark if r < 130 and g < 130 and b < 130 else light
    return image


def rgb(hex_colour: str) -> tuple[int, int, int]:
    value = hex_colour.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def vertical_gradient(
    im: Image.Image,
    box: tuple[int, int, int, int],
    start: str,
    end: str,
) -> None:
    x1, y1, x2, y2 = box
    sr, sg, sb = rgb(start)
    er, eg, eb = rgb(end)
    height = max(1, y2 - y1)
    grad = Image.new("RGB", (1, height))
    gp = grad.load()
    for y in range(height):
        t = y / max(1, height - 1)
        gp[0, y] = (
            round(sr + (er - sr) * t),
            round(sg + (eg - sg) * t),
            round(sb + (eb - sb) * t),
        )
    grad = grad.resize((x2 - x1, height))
    im.paste(grad, (x1, y1))


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask


def build_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGB", (W, H), CREAM)

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((58, 54, 1022, 1886), radius=42, fill=(26, 42, 35, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(20))
    im = Image.alpha_composite(im.convert("RGBA"), shadow).convert("RGB")

    card = Image.new("RGB", (984, 1836), PAPER)
    im.paste(card, (48, 40), rounded_mask(card.size, 40))

    header = Image.new("RGB", (984, 350), GREEN_DARK)
    vertical_gradient(header, (0, 0, 984, 350), "#0A4D3C", "#07382E")
    im.paste(header, (48, 40), rounded_mask(header.size, 40))
    # Square off the lower edge while keeping the top corners rounded.
    im.paste(header.crop((0, 300, 984, 350)), (48, 340))

    footer = Image.new("RGB", (984, 416), GREEN_DARK)
    vertical_gradient(footer, (0, 0, 984, 416), "#0A4B3C", "#062E26")
    im.paste(footer, (48, 1460), rounded_mask(footer.size, 40))
    im.paste(footer.crop((0, 0, 984, 55)), (48, 1460))

    d = ImageDraw.Draw(im)
    d.line((48, 390, 1032, 390), fill=GOLD, width=4)
    d.line((48, 1460, 1032, 1460), fill=GOLD, width=4)

    # Quiet geometric detail: visible enough to add depth, never enough to fight text.
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for inset, alpha in ((0, 44), (28, 28), (56, 20)):
        od.arc((820 + inset, -70 + inset, 1140 - inset, 250 - inset), 70, 260, fill=(196, 154, 74, alpha), width=3)
    for cx, cy in ((92, 315), (985, 92), (930, 330)):
        od.polygon(
            [(cx, cy - 11), (cx + 4, cy - 4), (cx + 11, cy), (cx + 4, cy + 4), (cx, cy + 11), (cx - 4, cy + 4), (cx - 11, cy), (cx - 4, cy - 4)],
            fill=(196, 154, 74, 70),
        )
    im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")
    return im, ImageDraw.Draw(im)


def draw_emblem(draw: ImageDraw.ImageDraw, language: str) -> None:
    draw.ellipse((95, 98, 211, 214), fill="#0B332A", outline=GOLD, width=3)
    draw.ellipse((107, 110, 199, 202), outline="#5E8B79", width=2)
    if language == "urdu":
        draw_rtl_anchor(draw, "ز", (153, 157), font(URDU_BOLD, 55), GOLD, "mm")
    else:
        draw.text((153, 157), "ZR", font=font(ROMAN_BOLD, 34), fill=GOLD, anchor="mm")


def draw_header(draw: ImageDraw.ImageDraw, language: str, date_text: str) -> None:
    draw_emblem(draw, language)
    if language == "urdu":
        draw_rtl_top(draw, "زادِ روز", 976, 84, font(URDU_BOLD, 78), WHITE)
        draw_rtl_top(draw, "دین و طب کی مختصر روزانہ رہنمائی", 976, 183, font(URDU, 34), "#DCE8E2")
        pill = (387, 278, 976, 340)
        draw.rounded_rectangle(pill, radius=22, fill="#F8F0DF", outline=GOLD, width=2)
        draw_rtl_anchor(draw, date_text, (950, 309), font(URDU_BOLD, 27), GREEN_DARK, "rm")
    else:
        draw.text((270, 92), "ZAD-E-ROZ", font=font(ROMAN_BOLD, 66), fill=WHITE, anchor="la")
        draw.text((270, 180), "Deen aur Tibb ki Mukhtasar Rozana Rehnumai", font=font(ROMAN, 31), fill="#DCE8E2", anchor="la")
        pill = (270, 276, 976, 338)
        draw.rounded_rectangle(pill, radius=22, fill="#F8F0DF", outline=GOLD, width=2)
        draw.text((295, 307), date_text, font=font(ROMAN_MEDIUM, 24), fill=GREEN_DARK, anchor="lm")


def draw_social_icon(draw: ImageDraw.ImageDraw, kind: str, x: int, y: int) -> None:
    if kind == "instagram":
        draw.rounded_rectangle((x, y, x + 34, y + 34), radius=9, outline=WHITE, width=3)
        draw.ellipse((x + 9, y + 9, x + 25, y + 25), outline=WHITE, width=3)
        draw.ellipse((x + 25, y + 6, x + 29, y + 10), fill=GOLD)
    elif kind == "x":
        draw.line((x + 4, y + 3, x + 31, y + 32), fill=WHITE, width=4)
        draw.line((x + 30, y + 3, x + 4, y + 32), fill=WHITE, width=4)
    elif kind == "youtube":
        draw.rounded_rectangle((x, y + 4, x + 38, y + 31), radius=8, fill=WHITE)
        draw.polygon([(x + 16, y + 10), (x + 16, y + 25), (x + 28, y + 17)], fill=GREEN_DARK)


def draw_social_strip(draw: ImageDraw.ImageDraw) -> None:
    y1, y2 = 1792, 1876
    draw.rectangle((48, y1, 1032, y2), fill="#062E26")
    draw.line((76, y1, 1004, y1), fill="#51766A", width=1)
    draw.line((372, y1 + 16, 372, y2 - 16), fill="#31584B", width=1)
    draw.line((706, y1 + 16, 706, y2 - 16), fill="#31584B", width=1)

    entries = [
        (92, "instagram", "@hakeem.zakii", 21),
        (407, "x", "@idoczaki", 22),
        (734, "youtube", "@SehatnamaByZaki", 19),
    ]
    for left, kind, handle, size in entries:
        icon_y = y1 + 25
        draw_social_icon(draw, kind, left, icon_y)
        draw.text((left + 50, y1 + 42), handle, font=font(ROMAN_MEDIUM, size), fill=WHITE, anchor="lm")


def draw_footer(im: Image.Image, draw: ImageDraw.ImageDraw, language: str, qr_img: Image.Image) -> None:
    qr_box = (78, 1522, 252, 1696)
    draw.rounded_rectangle(qr_box, radius=20, fill=PAPER, outline=GOLD, width=2)
    im.paste(qr_img, (90, 1534))
    draw.text((165, 1728), "Telegram", font=font(ROMAN, 17), fill="#B8CCC3", anchor="mm")
    draw.text((165, 1755), TELEGRAM, font=font(ROMAN_BOLD, 19), fill=GOLD, anchor="mm")

    left = 292
    draw.text((left, 1507), "PUBLISHED BY", font=font(ROMAN_BOLD, 16), fill=GOLD, anchor="la")
    draw.text((left, 1542), INSTITUTE_LINE_1, font=font(ROMAN_BOLD, 22), fill=WHITE, anchor="la")
    draw.text((left, 1576), f"{INSTITUTE_LINE_2}  •  {INSTITUTE_SITE}", font=font(ROMAN_MEDIUM, 20), fill="#DCE8E2", anchor="la")

    if language == "urdu":
        draw_rtl_top(draw, "مؤلف: حکیم محمد ذکی العثمانی", 988, 1622, font(URDU_BOLD, 27), WHITE)
        draw.text((left, 1682), AUTHOR_SITE, font=font(ROMAN_MEDIUM, 20), fill=GOLD, anchor="la")
    else:
        draw.text((left, 1630), "Muallif: Hakeem Muhammad Zaki Al Usmani", font=font(ROMAN_MEDIUM, 23), fill=WHITE, anchor="la")
        draw.text((left, 1672), AUTHOR_SITE, font=font(ROMAN_MEDIUM, 20), fill=GOLD, anchor="la")

    draw.text((left, 1732), f"CONTACT  •  {PHONE}", font=font(ROMAN_BOLD, 20), fill="#DCE8E2", anchor="la")
    draw_social_strip(draw)


def draw_urdu_content(draw: ImageDraw.ImageDraw, item: dict) -> None:
    draw_rtl_top(draw, item["label"], 976, 426, font(URDU_BOLD, 30), GOLD_DARK)

    hf = font(URDU_BOLD, 53)
    heading_lines = wrap_words(draw, item["heading"], hf, 850, True)
    hy = 476
    for line in heading_lines:
        draw_rtl_top(draw, line, 976, hy, hf, TEXT)
        hy += 72

    panel_top = max(602, hy + 20)
    panel_bottom = 1338
    draw.rounded_rectangle((104, panel_top, 976, panel_bottom), radius=30, fill=PANEL, outline="#D8C49A", width=2)
    draw.rectangle((104, panel_top + 28, 111, panel_bottom - 28), fill=GOLD)

    sf = font(URDU_BOLD, 29)
    pill_w = max(150, text_width(draw, item["section"], sf, True) + 72)
    draw.rounded_rectangle((976 - pill_w, panel_top, 976, panel_top + 72), radius=23, fill=GREEN)
    draw_rtl_anchor(draw, item["section"], (948, panel_top + 36), sf, WHITE, "rm")

    bf = font(URDU, 38)
    y = panel_top + 95
    line_height = 59
    for pidx, paragraph in enumerate(item["paragraphs"]):
        for line in wrap_words(draw, paragraph, bf, 792, True):
            draw_rtl_anchor(draw, line, (930, y), bf, TEXT, "ra")
            y += line_height
        if pidx < len(item["paragraphs"]) - 1:
            y += 14
    if y > panel_bottom - 28:
        raise RuntimeError(f"Urdu copy overflows the V2 template: {y} > {panel_bottom - 28}")


def draw_roman_content(draw: ImageDraw.ImageDraw, item: dict) -> None:
    draw.text((104, 433), item["label"].upper(), font=font(ROMAN_BOLD, 24), fill=GOLD_DARK, anchor="la")

    hf = font(ROMAN_BOLD, 50)
    heading_lines = wrap_words(draw, item["heading"], hf, 872, False)
    hy = 488
    for line in heading_lines:
        draw.text((104, hy), line, font=hf, fill=TEXT, anchor="la")
        hy += 64

    panel_top = max(608, hy + 23)
    panel_bottom = 1338
    draw.rounded_rectangle((104, panel_top, 976, panel_bottom), radius=30, fill=PANEL, outline="#D8C49A", width=2)
    draw.rectangle((104, panel_top + 28, 111, panel_bottom - 28), fill=GOLD)

    sf = font(ROMAN_BOLD, 25)
    pill_w = max(160, text_width(draw, item["section"], sf) + 70)
    draw.rounded_rectangle((104, panel_top, 104 + pill_w, panel_top + 66), radius=22, fill=GREEN)
    draw.text((138, panel_top + 33), item["section"], font=sf, fill=WHITE, anchor="lm")

    bf = font(ROMAN, 34)
    y = panel_top + 104
    line_height = 48
    for pidx, paragraph in enumerate(item["paragraphs"]):
        for line in wrap_words(draw, paragraph, bf, 774, False):
            draw.text((151, y), line, font=bf, fill=TEXT, anchor="la")
            y += line_height
        if pidx < len(item["paragraphs"]) - 1:
            y += 20
    if y > panel_bottom - 28:
        raise RuntimeError(f"Roman copy overflows the V2 template: {y} > {panel_bottom - 28}")


def draw_disclaimer(draw: ImageDraw.ImageDraw, language: str) -> None:
    draw.rounded_rectangle((104, 1365, 976, 1432), radius=22, fill=GREEN_PALE, outline="#C5DDD2", width=1)
    if language == "urdu":
        draw_rtl_anchor(
            draw,
            "عمومی تعلیمی رہنمائی؛ ذاتی طبی تشخیص یا علاج کا متبادل نہیں۔",
            (936, 1398),
            font(URDU, 26),
            MUTED,
            "rm",
        )
    else:
        draw.text(
            (540, 1398),
            "General education only; not a substitute for personal diagnosis or treatment.",
            font=font(ROMAN, 21),
            fill=MUTED,
            anchor="mm",
        )


def safe_save(im: Image.Image, path: Path) -> None:
    temp = path.with_name(f"{path.stem}.tmp.png")
    im.save(temp, "PNG", compress_level=6)
    with Image.open(temp) as check:
        check.verify()
    temp.replace(path)


def render(item: dict, path: Path, qr_img: Image.Image, date_text: str) -> None:
    im, draw = build_canvas()
    language = item["language"]
    draw_header(draw, language, date_text)
    if language == "urdu":
        draw_urdu_content(draw, item)
    else:
        draw_roman_content(draw, item)
    draw_disclaimer(draw, language)
    draw_footer(im, draw, language, qr_img)
    safe_save(im, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Zad-e-Roz Urdu and Roman social cards.")
    parser.add_argument(
        "--input",
        type=Path,
        help="Optional UTF-8 JSON payload. If omitted, the approved built-in payload is used.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = DEFAULT_PAYLOAD
    if args.input:
        payload = json.loads(args.input.read_text(encoding="utf-8"))

    slug = payload["date_slug"]
    cards = payload["cards"]
    qr_img = make_qr()
    outputs = []
    for key in ("urdu_deen", "urdu_tibb", "roman_deen", "roman_tibb"):
        language, section = key.split("_", 1)
        path = OUT_DIR / f"zad-e-roz-{language}-{section}-{slug}.png"
        date_text = payload["date_urdu"] if language == "urdu" else payload["date_roman"]
        render(cards[key], path, qr_img, date_text)
        outputs.append(str(path))

    manifest = OUT_DIR / f"zad-e-roz-{slug}-v2-manifest.json"
    manifest.write_text(
        json.dumps({"outputs": outputs, "payload": payload}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"outputs": outputs, "manifest": str(manifest)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()