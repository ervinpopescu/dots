#!/bin/python
import json
import subprocess

folder = "/home/ervin/Pictures/wallpapers/rand/"

find = ["find", folder, "-maxdepth", "1", "-type", "f", "!", "-iname", ".*"]
find_output = subprocess.check_output(find).decode("utf-8").strip()
image_paths = find_output.splitlines()
image_paths.sort(key=lambda s: s.casefold())

resolutions = []  # list of strings
for image in image_paths:
    resolutions = resolutions + (
        subprocess.check_output(["identify", "-format", "%wx%h", image])
        .decode("utf-8")
        .splitlines()
    )

image_names = find_output.replace(folder, "").splitlines()
image_names.sort(key=lambda s: s.casefold())
img_res = dict(zip(image_names, resolutions))
errors = ""

for res, key, value in zip(resolutions, img_res.keys(), img_res.values()):
    width = res.split("x")[0]
    height = res.split("x")[1]
    if int(width) < 1080 or int(height) < 1660:
        # img_res[key] = {"resolution": value, "error": "width or height not good"}
        # print("Error! " + folder + key + ": " + width + "x" + height)
        errors = errors + folder + key + "\n"
print(errors.strip())

# img_res_string = json.dumps(img_res, sort_keys=True, indent=2)
# outfile = open("resolutions.json", "w")
# outfile.write(img_res_string)
# print(img_res_string)
