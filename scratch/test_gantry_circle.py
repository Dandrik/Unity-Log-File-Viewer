import sys
import math
sys.path.insert(0, r"c:\Users\USNelRog\OneDrive - Elekta\Documents\source\repos\Unity Log File Viewer")
from PIL import Image, ImageDraw, ImageFont

def test_gantry_circle():
    w, h = 600, 320
    img = Image.new("RGB", (w, h), "#0f172a")
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("segoeui.ttf", 12)
        font_val = ImageFont.truetype("consola.ttf", 12)
        font_cardinal = ImageFont.truetype("segoeui.ttf", 9)
    except Exception:
        font_title = font_val = font_cardinal = ImageFont.load_default()

    def draw_gantry_card(ox, oy, angle_deg, error_deg=0.0):
        box_w = 270.0
        box_h = 210.0
        # Card background
        draw.rectangle([ox, oy, ox + box_w, oy + box_h], fill="#131d35", outline="#334155", width=1)

        # Header readout
        draw.text((ox + 14.0, oy + 12.0), "Gantry Angle:", fill="#94a3b8", font=font_title)
        val_str = f"{angle_deg:.1f}°"
        if abs(error_deg) > 0.01:
            val_str += f" ({error_deg:+.2f}°)"
        draw.text((ox + 104.0, oy + 12.0), val_str, fill="#38bdf8", font=font_val)

        # Black circle
        gcx = ox + (box_w / 2.0)
        gcy = oy + 115.0
        R = 52.0

        # Circle background
        draw.ellipse([gcx - R, gcy - R, gcx + R, gcy + R], fill="#000000", outline="#475569", width=2)

        # Cardinal ticks & labels
        cardinals = [
            (0,   "0°",   gcx,         gcy - R - 8,  "s"),
            (90,  "90°",  gcx + R + 8, gcy,          "w"),
            (180, "180°", gcx,         gcy + R + 8,  "n"),
            (270, "270°", gcx - R - 8, gcy,          "e"),
        ]
        for c_ang, c_lbl, lx, ly, anchor in cardinals:
            rad_c = math.radians(c_ang)
            # Tick on circle edge
            tx1 = gcx + (R - 4) * math.sin(rad_c)
            ty1 = gcy - (R - 4) * math.cos(rad_c)
            tx2 = gcx + R * math.sin(rad_c)
            ty2 = gcy - R * math.cos(rad_c)
            draw.line([tx1, ty1, tx2, ty2], fill="#64748b", width=1)

            bbox = draw.textbbox((0, 0), c_lbl, font=font_cardinal)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            if anchor == "s":
                tx, ty = lx - tw/2, ly - th
            elif anchor == "n":
                tx, ty = lx - tw/2, ly
            elif anchor == "w":
                tx, ty = lx, ly - th/2
            elif anchor == "e":
                tx, ty = lx - tw, ly - th/2
            draw.text((tx, ty), c_lbl, fill="#64748b", font=font_cardinal)

        # Subtle isocenter crosshair in center of black circle
        draw.line([gcx - 5, gcy, gcx + 5, gcy], fill="#334155", width=1)
        draw.line([gcx, gcy - 5, gcx, gcy + 5], fill="#334155", width=1)
        draw.ellipse([gcx - 2, gcy - 2, gcx + 2, gcy + 2], fill="#475569")

        # Red arrow pointing IN from the black circle towards the center
        rad = math.radians(angle_deg)
        # Source position at perimeter
        sx = gcx + (R - 2) * math.sin(rad)
        sy = gcy - (R - 2) * math.cos(rad)

        # Target position near center
        r_end = 12.0
        ex = gcx + r_end * math.sin(rad)
        ey = gcy - r_end * math.cos(rad)

        # Arrow shaft
        draw.line([sx, sy, ex, ey], fill="#ef4444", width=3)

        # Source dot at perimeter
        draw.ellipse([sx - 4, sy - 4, sx + 4, sy + 4], fill="#ef4444", outline="#fca5a5")

        # Arrowhead pointing towards center
        # Direction vector towards center: (-sin(rad), cos(rad))
        ux = -math.sin(rad)
        uy = math.cos(rad)
        # Perpendicular vector: (-uy, ux)
        px = -uy
        py = ux

        head_len = 10.0
        head_w = 6.0
        p_tip = (ex, ey)
        p_base1 = (ex - (ux * head_len) + (px * head_w), ey - (uy * head_len) + (py * head_w))
        p_base2 = (ex - (ux * head_len) - (px * head_w), ey - (uy * head_len) - (py * head_w))
        draw.polygon([p_tip, p_base1, p_base2], fill="#ef4444")

    # Draw two angles: e.g. 45° and 225°
    draw_gantry_card(15, 15, 45.0, 0.02)
    draw_gantry_card(305, 15, 225.0, -0.05)

    out_path = r"C:\Users\USNelRog\.gemini\antigravity\brain\c567f6a1-c942-496b-8f5e-d9906f3a9fee\gantry_circle_preview.png"
    img.save(out_path)
    print("Saved gantry circle preview to:", out_path)

if __name__ == "__main__":
    test_gantry_circle()

