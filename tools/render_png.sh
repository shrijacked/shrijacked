#!/bin/bash
# usage: render.sh in.svg out.png
f=$(readlink -f "$1"); W=$(grep -o 'width="[0-9]*"' "$f" | head -1 | tr -dc 0-9); H=$(grep -o 'height="[0-9]*"' "$f" | head -1 | tr -dc 0-9)
echo "<html><body style='margin:0;background:transparent'><img src='file://$f'></body></html>" > /tmp/wrap.html
timeout 60 google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars --allow-file-access-from-files --force-device-scale-factor=2 --default-background-color=00000000 --window-size=$W,$H --virtual-time-budget=2000 --screenshot="$(readlink -f "$2")" file:///tmp/wrap.html >/dev/null 2>&1
