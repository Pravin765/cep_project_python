"""Upload demo assets to Cloudinary. Requires CLOUDINARY_URL env var."""
import os, sys
import cloudinary, cloudinary.uploader

if not os.environ.get("CLOUDINARY_URL"):
    sys.exit("CLOUDINARY_URL is not set.")

cloudinary.config(secure=True)
FOLDER = "cep_rural_startups/demos"

ASSETS = [
    ("static/demos/auto_crop.mp4",           "video"),
    ("static/demos/withoutbg_bulk_demo.mp4", "video"),
    ("static/demos/dslr_renamer_demo.mp4",   "video"),
    ("static/demos/class_mgmt_site.png",     "image"),
]

results = {}
for path, rtype in ASSETS:
    if not os.path.exists(path):
        print(f"!! missing: {path}")
        continue
    res = cloudinary.uploader.upload(path, folder=FOLDER, resource_type=rtype,
                                      use_filename=True, unique_filename=False, overwrite=True)
    results[path] = res["secure_url"]
    print(f"{path}  ->  {res['secure_url']}")

print("\n===== Render env vars =====\n")
for k, pth in [("DEMO_VIDEO_CROP_URL", "static/demos/auto_crop.mp4"),
               ("DEMO_VIDEO_BG_URL",   "static/demos/withoutbg_bulk_demo.mp4"),
               ("DEMO_VIDEO_RENAMER_URL", "static/demos/dslr_renamer_demo.mp4"),
               ("DEMO_SITE_IMAGE_URL", "static/demos/class_mgmt_site.png")]:
    print(f"{k}={results.get(pth, '')}")
