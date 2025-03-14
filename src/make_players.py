import plistlib
import os
import csv
import sys
import pprint
import requests
import re
import pyvips
from PIL import Image as PILImage
from io import BytesIO
import pathlib
import traceback
import face_recognition
from util import crop_image, resize_image, import_castlist

"""

This is designed to convert a CSV of a cast list with optional comments and images
and convert it into a .pla file that can be imported into WaveTool 3.

"""


def create_wavetool_castlist(castlist, output_file, castlist_path):
    with open(
        os.path.join(
            str(pathlib.Path(__file__).parent.resolve()), "../defaultimage.tiff"
        ),
        "rb",
    ) as image:
        default_image = image.read()
    wavetool_castlist = []
    for row in castlist:
        print(f"Processing {row['character']} played by {row['real_name']}")
        print(f"Image path is {row['image']}")
        image = default_image
        if row["image"] is not None:
            if re.match(r"^(http|https)\:\/\/", row["image"]):
                # url is online, so we'll use requests to get the image
                try:
                    print(
                        "  Downloading image from " + row["image"] + "... ",
                        end="",
                    )
                    r = requests.get(row["image"])
                    if r.ok:
                        image = r.content

                        print("Success!")
                    else:
                        print("Failed!")
                except Exception as e:
                    print("Failed! {}\n".format(e))
            else:
                try:
                    image_path = row["image"]
                    if not os.path.exists(image_path):
                        image_path = os.path.join(castlist_path, row["image"])
                    character_image_fp = open(image_path, "rb")
                    image = character_image_fp.read()
                    character_image_fp.close()
                except IOError:
                    image = default_image
        if row["crop"]:
            print(
                "Cropping image for {} to remove whitespace".format(
                    row["real_name"]
                )
            )
            try:
                image = crop_image(image)
            except:
                traceback.print_exc()
                print("Error cropping image")
                sys.exit(1)
        if row["resize"]:
            print("Resizing image for {} to 512x512".format(row["real_name"]))
            image = resize_image(image)
        cast_dict = dict(
            Comments=row["comments"],
            Compressed=False,
            Image=image,
            Name=row["real_name"],
            RoleName=row["character"],
            Scaled=False,
            Version=1,
        )
        wavetool_castlist.append(cast_dict)
    plistlib.dump(wavetool_castlist, output_file)


if __name__ == "__main__":
    # Import castlist from CSV file

    if len(sys.argv) < 3:
        print("Usage: python make_players.py <castlist.csv> <output.pla>")
        exit(1)

    if sys.argv[1] == None:
        print("No castlist file specified")
        exit(1)

    if sys.argv[2] == None:
        print("No output file specified")
        exit(1)

    castlist_file = sys.argv[1]
    output_file = sys.argv[2]
    castlist = import_castlist(castlist_file)
    castlist_path = pathlib.Path(castlist_file).parent.resolve()
    if os.path.isfile(output_file):
        overwrite = input(
            "Output file already exists. Do you want to overwrite? (y/n): "
        )
        if overwrite != "y":
            exit(0)
    try:
        output_file_handler = open(output_file, "wb")
        create_wavetool_castlist(castlist, output_file_handler, castlist_path)
    except IOError:
        print("Could not open file: " + output_file)
        traceback.print_exc()
        exit(1)
