# Templates (Zack D. quality)

Each template is a reusable `.blend` with locked style:

- Film / EEVEE or Cycles look-dev that matches channel grade  
- Camera + DOF already framed for **1080×1920**  
- Soft rim light, clean materials (clay / stylized plastic OK)  
- Empty **collection sockets** for free models (swap per episode)  
- Markers or named cameras: `CAM_HOOK`, `CAM_EXPLAIN`, `CAM_CLOSE`

## Required starter templates

| File | Use |
|------|-----|
| `body_gentle.blend` | Kid-safe body / sneeze / heart beat (no gore) |
| `space.blend` | Planets, stars, simple solar system |
| `animals.blend` | Friendly animal + habitat |
| `classroom.blend` | Desk, globe, simple props |
| `earth_weather.blend` | Clouds, rain cycle, seasons |
| `shapes_colors.blend` | Ages 1–5 only |

Put files in `blender/templates/`.

Starter generator (needs Blender on PATH or `BLENDER_PATH`):

```powershell
python main.py --check
python main.py --build-templates
```

`body_gentle.blend` is built from primitives in `blender/scripts/build_body_gentle_template.py` (kid-safe vinyl toy + dust + air puff). Treat it as look-dev until lighting passes the paused-frame-1 test.

## Per-episode difference

Automation should change at least:

1. Topic / narration  
2. Which free models are linked  
3. Camera cut list  
4. Accent color  
5. Duration of shots  

Same template ≠ same video.

## Quality checklist before shipping a template

- [ ] Looks good paused on frame 1 (thumbnail test)  
- [ ] No muddy lighting  
- [ ] Readable silhouette on phone  
- [ ] No scary / gross medical detail for under-10  
- [ ] Renders under ~10–20 min on your PC for a 45s Short (tune samples)  
