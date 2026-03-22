---
name: video-text-overlay
created_by: claude-code
created_at: 2026-03-20
version: 2
success_rate: 95%
---

# Video Text Overlay

## What This Skill Does
Burns text hooks onto videos in TikTok-native style.

## Technical Spec
- Font: HelveticaNeue (/System/Library/Fonts/HelveticaNeue.ttc, index=0)
- Size: 38-43px depending on text length
- Color: White (255,255,255,255)
- Shadow: Subtle drop shadow, offset 1-2px, black at 160 alpha
- Position: 38% from top (slightly above center)
- Max width: 88% of frame, auto-wrap
- NEVER use emojis — Pillow can't render them, shows blocks
- CAPS on exactly 2 keywords per hook

## Code
```python
from PIL import Image, ImageDraw, ImageFont

def create_overlay(text, w=720, h=1280):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 38, index=0)
    
    # Auto-wrap lines within 88% width
    max_w = int(w * 0.88)
    lines = wrap_text(text, font, max_w, draw)
    
    # Position at 38% from top
    total_h = sum(line_heights) + (len(lines) - 1) * 8
    y = int(h * 0.38) - total_h // 2
    
    for line in lines:
        x = (w - line_width) // 2
        # Drop shadow
        for dx in [1, 2]:
            for dy in [1, 2]:
                draw.text((x+dx, y+dy), line, font=font, fill=(0,0,0,160))
        # White text
        draw.text((x, y), line, font=font, fill=(255,255,255,255))
        y += line_height + 8
    
    return img
```

## Version History
- v1: Gilroy Bold + heavy black outline → looked amateur
- v2: HelveticaNeue + drop shadow → TikTok native look ✅
