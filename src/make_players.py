import plistlib
import os
import csv
import sys
import pprint
import requests
import re

"""

This is designed to convert a CSV of a cast list with optional comments and images
and convert it into a .pla file that can be imported into WaveTool 3.

"""


def import_castlist(castlist_file):
    # Import castlist from CSV file
    castlist = []
    with open(castlist_file, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            real_name = ""
            character = ""
            comments = ""
            image = None
            if "Real Name" in row:
                real_name = row["Real Name"]
            if "Character" in row:
                character = row["Character"]
            if "Comments" in row:
                comments = row["Comments"]
            if "Image" in row:
                image = row["Image"]
            if real_name == "" and character == "":
                continue
            character = {
                "character": character,
                "real_name": real_name,
                "comments": comments,
                "image": image,
            }
            castlist.append(character)
    return castlist


def create_wavetool_castlist(castlist, output_file):
    with open("defaultimage.tiff", "rb") as image:
        default_image = image.read()
    wavetool_castlist = []
    for row in castlist:
        print(f"Processing {row['character']} played by {row['real_name']}")
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
                    character_image_fp = open(row["image"], "rb")
                    image = character_image_fp.read()
                    character_image_fp.close()
                except IOError:
                    image = default_image
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
    if os.path.isfile(output_file):
        overwrite = input(
            "Output file already exists. Do you want to overwrite? (y/n): "
        )
        if overwrite != "y":
            exit(0)
    try:
        output_file_handler = open(output_file, "wb")
        create_wavetool_castlist(castlist, output_file_handler)
    except IOError:
        print("Could not open file: " + output_file)
        exit(1)
