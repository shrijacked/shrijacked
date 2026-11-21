#!/bin/bash
# One-shot: photo -> ASCII variants -> portrait.txt -> SVGs -> PNG previews.
# usage: tools/make_all.sh /path/to/photo.png [variant]   (default variant: c46_andrew_forlight)
set -e
cd "$(dirname "$0")/.."
PHOTO="$1"; VAR="${2:-c46_andrew_forlight}"
/workspace/venv-ascii/bin/python tools/ascii_portrait.py "$PHOTO" variants
cp "variants/variant_${VAR}.txt" portrait.txt
python3 build_svg.py
tools/render_png.sh dark_mode.svg preview/dark_mode.png
tools/render_png.sh light_mode.svg preview/light_mode.png
echo "variants sheet: $(pwd)/variants/variants_sheet.png"
echo "previews: $(pwd)/preview/dark_mode.png  $(pwd)/preview/light_mode.png"
