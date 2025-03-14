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
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from util import crop_image, resize_image, import_castlist

"""

This is designed to convert a CSV of a cast list with optional comments and images
and convert it into a .pla file that can be imported into WaveTool 3.

"""


def create_mic_cards(castlist, output_file, castlist_path):
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
            Channel=row["channel"],
            Version=1,
        )
        wavetool_castlist.append(cast_dict)
    pdf = FPDF(format="A4")
    pdf.set_top_margin(25)
    pdf.set_left_margin(25)
    pdf.set_right_margin(25)
    bg_path = os.path.join(
        str(pathlib.Path(__file__).parent.resolve()), "../pdfbg.svg"
    )
    pdf.set_page_background(bg_path)
    for character in wavetool_castlist:
        pdf.add_page()
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(
            0,
            10,
            text=f"Channel {character['Channel']}",
            new_y=YPos.NEXT,
            new_x=XPos.LMARGIN,
            align="R",
        )
        pdf.set_font("helvetica", "B", 24)
        pdf.cell(
            0,
            10,
            text=character["RoleName"],
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            align="C",
        )
        pdf.set_font("helvetica", "", 12)
        pdf.cell(
            0,
            10,
            text=character["Name"],
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            align="C",
        )
        pdf.cell(
            0,
            10,
            text=character["Comments"],
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            align="C",
        )
        box = 75
        pdf.image(
            character["Image"],
            w=box,
            h=box,
            x=pdf.w / 2 - box / 2,
            keep_aspect_ratio=True,
        )
    pdf.output(output_file)


if __name__ == "__main__":
    # Import castlist from CSV file

    if len(sys.argv) < 3:
        print("Usage: python make_players.py <castlist.csv> <output.pdf>")
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
        create_mic_cards(castlist, output_file_handler, castlist_path)
    except IOError:
        print("Could not open file: " + output_file)
        traceback.print_exc()
        exit(1)
