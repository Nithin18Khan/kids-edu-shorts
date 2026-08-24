# Templates

Drop reusable `.blend` files here, or generate the starter:

```powershell
python main.py --build-templates
```

That runs `blender/scripts/build_body_gentle_template.py` and writes:

- `body_gentle.blend` — vinyl-toy character, dust, air puff, `CAM_HOOK` / `CAM_EXPLAIN` / `CAM_CLOSE`
- `previews/body_gentle_frame1.png` — thumbnail / lighting check

See `docs/TEMPLATES.md` for the quality bar.

`body_gentle` is a high-key teal studio with unique cameras per beat (hook / profile / macro / blast / car / close), clay SSS, and rim light. Captions are burned in at assemble (Zack-style yellow word highlight). Still look-dev — not a claim of matching Zack D. Films.
