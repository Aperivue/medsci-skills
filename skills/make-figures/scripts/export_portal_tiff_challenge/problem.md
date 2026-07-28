# Challenge — portal-ready TIFF export (LZW + RGBA→RGB white-flatten)

A submission portal rejects a figure and the author cannot see why. Two facts collide at
the upload button:

1. The portal accepts only `.jpeg` / `.tiff` / `.eps` — **not** the `.png` the figure was
   rendered as (Springer Nature SNAPP does exactly this).
2. The portal caps a figure at 25 MB (JACC: Asia). A raw, uncompressed 600-dpi **RGBA**
   TIFF sails past the cap; the same pixels saved **LZW-compressed** with the alpha channel
   **flattened onto white** are a fraction of the size — and a TIFF that keeps its alpha
   renders the transparent regions **black** on many production pipelines.

`export_portal_tiff.py` does the conversion a human otherwise does by hand in Photoshop, and
then **proves** the result is pixel-identical to that white-flatten before handing it over.

## What `verify.sh` asserts (network-free, Pillow-only)

Positive — on a synthetic RGBA PNG with a transparent quadrant and a colour gradient:

- the output is a **TIFF**, mode **RGB** (no alpha), **LZW**-compressed (Compression tag 5);
- the once-transparent region is now **white** and the opaque pixels are unchanged;
- the LZW output is strictly **smaller** than an uncompressed TIFF of the same pixels.

Negative — the assertions must bite, not merely pass:

- flattening the same source onto **black** yields **different** bytes, so the pixel-identity
  check would have caught a wrong background or an ignored alpha channel;
- with `--max-mb` set below the output size, the exporter **refuses (exit 1)** rather than
  handing back a file that will bounce at the portal.

Skips cleanly if Pillow is unavailable (the same runtime dependency every raster figure
helper in this skill already carries).
