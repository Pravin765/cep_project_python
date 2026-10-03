from pathlib import Path
import sys

p = Path("templates/field_work.html")
if not p.exists():
    sys.exit("!! templates/field_work.html not found. Run this from the project root.")

s = p.read_text(encoding="utf-8")

OLD = '<div class="h-44 bg-indigo-900/5 overflow-hidden">'
NEW = '<div class="aspect-[4/3] bg-indigo-900/5 flex items-center justify-center overflow-hidden">'

if OLD not in s and 'aspect-[4/3]' in s:
    print("[--] already patched")
    sys.exit(0)

if OLD not in s:
    sys.exit("!! could not find the image container — did you already edit it?")

s = s.replace(OLD, NEW, 1)
s = s.replace('class="w-full h-full object-cover"',
              'class="w-full h-full object-contain"', 1)

p.write_text(s, encoding="utf-8")
print("[OK] field_work.html patched — photos will now display in full")

# quick verify
if 'aspect-[4/3]' in p.read_text(encoding="utf-8"):
    print("[OK] verification passed")