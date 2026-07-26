
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops
import math, os

ROOT = "/Users/alain/Mes Pojets IA/Loan Manager"
OUT = os.path.join(ROOT, "docs/screenshots/banner.png")
BW, BH = 2400, 1000

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))

top = (13, 20, 33)
mid = (23, 45, 80)
bot = (11, 24, 48)

bg = Image.new("RGB", (BW, BH), top)
px = bg.load()
for y in range(BH):
    t = y / (BH-1)
    c = lerp(top, mid, t) if t < 0.55 else lerp(mid, bot, (t-0.55)/0.45)
    for x in range(BW):
        sheen = math.sin((x/(BW-1))*math.pi) * 16
        px[x,y] = tuple(max(0,min(255,c[i]+int(sheen))) for i in range(3))

def font(size, bold=False):
    path = "/System/Library/Fonts/Helvetica.ttc" if bold else "/System/Library/Fonts/HelveticaNeue.ttc"
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)

f_title = font(126, True)
f_tag = font(44, False)
pf = font(30, True)
f_logo = font(56, True)

draw = ImageDraw.Draw(bg)

# Logo mark: rounded gradient square with bank/landmark glyph (simple)
lx, ly = 120, 130
logo_size = 96
logo = Image.new("RGBA", (logo_size, logo_size), (0,0,0,0))
ld = ImageDraw.Draw(logo)
ld.rounded_rectangle([0,0,logo_size-1,logo_size-1], radius=24, fill=(40,120,220))
# simple columns/roof glyph
roof_y = 30
ld.polygon([(logo_size//2, 16),(16, roof_y),(logo_size-16, roof_y)], fill=(255,255,255))
cols = [22, 41, 59, 78]
for cx in cols:
    ld.rounded_rectangle([cx, roof_y+10, cx+10, logo_size-26], radius=4, fill=(255,255,255))
ld.rounded_rectangle([14, logo_size-26, logo_size-14, logo_size-16], radius=3, fill=(255,255,255))
bg.paste(logo, (lx, ly), logo)

title = "Lending Pro Freeware"
tx, ty = lx + logo_size + 26, ly - 6
glow = Image.new("RGB", (BW,BH), (0,0,0))
gd = ImageDraw.Draw(glow)
gd.text((tx, ty), title, font=f_title, fill=(40,120,220))
glow = glow.filter(ImageFilter.GaussianBlur(18))
bg = ImageChops.screen(bg, glow)
draw = ImageDraw.Draw(bg)
draw.text((tx, ty), title, font=f_title, fill=(245, 248, 252))

tag = "Private, offline-first loan & repayment management for lenders."
draw.text((tx+2, ty+160), tag, font=f_tag, fill=(180, 200, 225))

pills = ["100% Offline", "22 Currencies", "17 Languages", "Webcam Capture", "PDF Contracts", "Free Forever", "Multi-profile", "Local Backup"]
# two rows, left-aligned, confined to left half (max x ~ 1180)
max_x = 1180
row_y = [ty+160+90, ty+160+90+70]
cur_x = tx+2
cur_row = 0
for p in pills:
    pb = draw.textbbox((0,0), p, font=pf)
    pw = pb[2]-pb[0]
    pad_x = 26
    box_w, box_h = pw+pad_x*2, 50
    if cur_x + box_w > max_x:
        cur_row += 1
        cur_x = tx+2
        if cur_row > 1:
            break
    layer = Image.new("RGBA", (box_w, box_h), (0,0,0,0))
    ld2 = ImageDraw.Draw(layer)
    ld2.rounded_rectangle([0,0,box_w-1,box_h-1], radius=box_h//2, width=2, outline=(120,160,210), fill=(120,170,230,38))
    bg.paste(layer, (cur_x,row_y[cur_row]), layer)
    draw = ImageDraw.Draw(bg)
    draw.text((cur_x+pad_x, row_y[cur_row]+11), p, font=pf, fill=(225, 238, 252))
    cur_x += box_w + 16

shots = ["dashboard-demo.png", "loans.png", "payments.png"]
target_w = 720
imgs = []
for name in shots:
    im = Image.open(os.path.join(ROOT, "docs/screenshots", name)).convert("RGB")
    ratio = target_w / im.width
    im = im.resize((target_w, int(im.height*ratio)), Image.LANCZOS)
    imgs.append(im)

card_x_base = BW - 880
card_y_base = 165
gap = 32
card_h = imgs[0].height

bg = bg.convert("RGBA")
for i, im in enumerate(imgs):
    framed = ImageOps.expand(im, border=14, fill=(255,255,255))
    sh = Image.new("RGBA", (framed.width+60, framed.height+60), (0,0,0,0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([30,30,30+framed.width, 30+framed.height], radius=24, fill=(0,0,0,150))
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    ang = -8 + i*8
    rot = framed.rotate(ang, expand=True, resample=Image.BICUBIC, fillcolor=(0,0,0,0))
    rot_sh = sh.rotate(ang, expand=True, resample=Image.BICUBIC)
    y = card_y_base + i*(card_h//2 + gap)
    bg.alpha_composite(rot_sh, (card_x_base-40, y-20))
    bg.alpha_composite(rot.convert("RGBA"), (card_x_base-10, y))

bg.convert("RGB").save(OUT, "PNG", optimize=True)
print("saved", OUT, bg.size)
