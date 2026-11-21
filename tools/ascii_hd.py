"""High-res ASCII portrait: python ascii_hd.py PHOTO COLS -> portrait_dark.txt, portrait_light.txt"""
import sys, numpy as np, cv2
from PIL import Image, ImageOps
from rembg import remove
src, cols = sys.argv[1], int(sys.argv[2]); PCW, PLH = float(sys.argv[3]), float(sys.argv[4])
im = ImageOps.exif_transpose(Image.open(src)).convert("RGB"); im.thumbnail((1600,1600))
cut = remove(im); a = np.array(cut)[:,:,3]
ys, xs = np.where(a>40); y0,y1,x0,x1 = ys.min(),ys.max(),xs.min(),xs.max()
y1c = min(y1, y0+int((x1-x0)*1.05))
cut = cut.crop((max(0,x0-6),max(0,y0-6),min(cut.width,x1+6),y1c))
rgba = np.array(cut).astype(np.float32); alpha = rgba[:,:,3]/255
gray = cv2.cvtColor(rgba[:,:,:3].astype(np.uint8), cv2.COLOR_RGB2GRAY)
gray = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8)).apply(gray)
bl = cv2.GaussianBlur(gray,(0,0),2); gray = cv2.addWeighted(gray,1.8,bl,-0.8,0)
rows = int(round(cols*cut.height/cut.width*PCW/PLH))
lum = cv2.resize(gray.astype(np.float32)/255,(cols,rows),interpolation=cv2.INTER_AREA)
al = cv2.resize(alpha,(cols,rows),interpolation=cv2.INTER_AREA)
m = al>0.5; lo,hi = np.percentile(lum[m],2),np.percentile(lum[m],98)
lum = np.clip((lum-lo)/(hi-lo),0,1)
import os
RAMP = os.environ.get("RAMP", " .:-=+*#%@")
def out(ink, g):
    ink = (ink**g)*(al>0.35); n=len(RAMP)-1
    return "\n".join("".join(RAMP[int(round(v*n))] for v in r).rstrip() for r in ink)+"\n"
open("portrait_dark.txt","w").write(out(lum,1.1))     # bright skin -> dense glyphs on dark bg
open("portrait_light.txt","w").write(out(1-lum,0.9))   # dark hair -> dense glyphs on light bg
print(cols, rows)
