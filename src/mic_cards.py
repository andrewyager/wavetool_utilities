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

"""

This is designed to convert a CSV of a cast list with optional comments and images
and convert it into a .pla file that can be imported into WaveTool 3.

"""


def crop_image(image_buffer):

    # Load image and crop to remove whitespace
    image = face_recognition.load_image_file(BytesIO(image_buffer))
    face_locations = face_recognition.face_locations(image)
    image = PILImage.open(BytesIO(image_buffer))
    if len(face_locations) == 0:
        print("No faces found in image")
        new_buffer = BytesIO()
        image.save(new_buffer, "JPEG")
        return new_buffer.getvalue()
    top, right, bottom, left = face_locations[0]
    face_width = right - left
    face_height = bottom - top
    # Expand the bounding box by 50%
    left = max(0, left - (face_width / 2))
    right = min(image.width, right + (face_width / 2))
    top = max(0, top - (face_height / 2))
    bottom = min(image.height, bottom + (face_height / 2))
    print(left, right, top, bottom)

    image = image.crop((left, top, right, bottom))
    new_buffer = BytesIO()
    image.save(new_buffer, "JPEG")
    return new_buffer.getvalue()

    try:
        image = pyvips.Image.new_from_buffer(image_buffer, "")
    except:
        print("Could not load image with pyvips")
        sys.exit(1)
    try:
        background = image.getpoint(0, 0)
        width = image.width
        height = image.height
        # 30% background threshold
        mask = (image.gaussblur(60) - background).abs() > 30
        columns, rows = mask.project()
        left = columns.profile()[1].min()
        right = columns.width - columns.flip("horizontal").profile()[1].min()
        top = rows.profile()[0].min()
        bottom = rows.height - rows.flip("vertical").profile()[0].min()
        image = image.crop(left, top, right - left, bottom - top)
        print(
            "Original width/height was ({}, {}). New bounds are ({},{}), ({},{})".format(
                width, height, left, top, right, bottom
            )
        )
    except:
        print("Error processing whitespace")
        sys.exit(1)
    try:
        image = image.write_to_buffer(".jpg")
    except:
        print("Error writing to buffer")
        sys.exit(1)
    return image


def resize_image(image_buffer):
    image = PILImage.open(BytesIO(image_buffer))
    image.thumbnail((512, 512))
    new_buffer = BytesIO()
    image.save(new_buffer, "JPEG")
    return new_buffer.getvalue()


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
            crop = False
            resize = False
            channel = ""
            if "Real Name" in row:
                real_name = row["Real Name"]
            if "Character" in row:
                character = row["Character"]
            if "Comments" in row:
                comments = row["Comments"]
            if "Image" in row:
                image = row["Image"]
            if "Crop" in row:
                crop = row["Crop"] == "1"
            else:
                crop = True
            if "Resize" in row:
                resize = row["Resize"] == "1"
            else:
                resize = False
            if "Channel" in row:
                channel = row["Channel"]
            if real_name == "" and character == "":
                continue
            character = {
                "character": character,
                "real_name": real_name,
                "comments": comments,
                "image": image,
                "crop": crop,
                "resize": resize,
                "channel": channel,
            }
            castlist.append(character)
    return castlist


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
