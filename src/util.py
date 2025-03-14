import csv
from io import BytesIO
from PIL import Image as PILImage
import face_recognition
import os
import pathlib
import re
import requests
import traceback
import sys
import logging

logger = logging.getLogger("util")


def import_castlist(castlist_file, default_resize=True):
    """
    Import a cast list from a CSV file.
    For each row, it extracts:
      - "Real Name"
      - "Character"
      - "Comments"
      - "Image" (if provided)
      - "Crop" (default True if not specified)
      - "Resize" (default as per default_resize parameter)
      - "Channel" (if present; defaults to an empty string)
    Returns a list of dictionaries.
    """
    castlist = []
    with open(castlist_file, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            real_name = row.get("Real Name", "").strip()
            character = row.get("Character", "").strip()
            comments = row.get("Comments", "").strip()
            image = row.get("Image", "").strip() or None
            crop = row.get("Crop", "1") == "1"  # default True
            resize = row.get("Resize", "1" if default_resize else "0") == "1"
            channel = row.get("Channel", "").strip()
            if real_name == "" and character == "":
                continue
            castlist.append(
                {
                    "character": character,
                    "real_name": real_name,
                    "comments": comments,
                    "image": image,
                    "crop": crop,
                    "resize": resize,
                    "channel": channel,
                }
            )
    return castlist


def crop_image(image_buffer):
    from io import BytesIO
    from PIL import Image as PILImage
    import face_recognition

    if not image_buffer:
        logger.info("Debug: Empty image buffer.")
        return image_buffer

    try:
        pil_image = PILImage.open(BytesIO(image_buffer))
        logger.info(f"Debug: Successfully opened image. Size: {pil_image.size}")
    except Exception as e:
        logger.info(f"Debug: Could not open image from buffer. Error: {e}")
        return image_buffer

    try:
        image_array = face_recognition.load_image_file(BytesIO(image_buffer))
    except Exception as e:
        logger.info(
            f"Debug: face_recognition.load_image_file failed. Error: {e}"
        )
        return image_buffer

    try:
        face_locations = face_recognition.face_locations(
            image_array, number_of_times_to_upsample=0, model="cnn"
        )
        logger.info(f"Debug: Detected face locations: {face_locations}")
    except RuntimeError as e:
        logger.info(
            f"Debug: RuntimeError in face_recognition.face_locations: {e}"
        )
        return image_buffer

    if not face_locations:
        logger.info("Debug: No faces found in image. Skipping crop.")
        new_buffer = BytesIO()
        pil_image.save(new_buffer, "JPEG")
        return new_buffer.getvalue()

    top, right, bottom, left = face_locations[0]
    face_width = right - left
    face_height = bottom - top
    left = max(0, left - (face_width / 2))
    right = min(pil_image.width, right + (face_width / 2))
    top = max(0, top - (face_height / 2))
    bottom = min(pil_image.height, bottom + (face_height / 2))
    logger.info(
        f"Debug: Cropping image with box coordinates: left={left}, top={top}, right={right}, bottom={bottom}"
    )

    cropped = pil_image.crop((left, top, right, bottom))
    if cropped.mode == "RGBA":
        cropped = cropped.convert("RGB")
    new_buffer = BytesIO()
    cropped.save(new_buffer, "JPEG")
    return new_buffer.getvalue()


def resize_image(image_buffer):
    image = PILImage.open(BytesIO(image_buffer))
    image.thumbnail((512, 512))
    new_buffer = BytesIO()
    image.save(new_buffer, "JPEG")
    return new_buffer.getvalue()


def build_castlist(castlist, castlist_path):
    """
    Given an imported cast list (list of dictionaries) and the directory (as a Path)
    where the CSV file is located, process each row to download and process images.
    Returns a new list (wavetool_castlist) that is used for output generation.
    """
    default_image_path = os.path.join(
        str(pathlib.Path(__file__).parent.resolve()), "../defaultimage.tiff"
    )
    with open(default_image_path, "rb") as image_fp:
        default_image = image_fp.read()

    wavetool_castlist = []
    for row in castlist:
        logger.info(
            f"Processing {row['character']} played by {row['real_name']}"
        )
        img_data = default_image
        if row["image"] is not None:
            if re.match(r"^(http|https)://", row["image"]):
                try:
                    logger.info(f"  Downloading image from {row['image']}...")
                    r = requests.get(row["image"])
                    if r.ok:
                        img_data = r.content
                        logger.info("Success!")
                    else:
                        logger.info("Failed!")
                except Exception as e:
                    logger.info(f"Failed! {e}")
            else:
                try:
                    image_path = row["image"]
                    if not os.path.exists(image_path):
                        image_path = os.path.join(castlist_path, row["image"])
                    with open(image_path, "rb") as img_fp:
                        img_data = img_fp.read()
                except IOError:
                    img_data = default_image
        if row["crop"]:
            logger.info(
                f"Cropping image for {row['real_name']} to remove whitespace"
            )
            try:
                img_data = crop_image(img_data)
            except Exception:
                traceback.print_exc()
                logger.info("Error cropping image")
                sys.exit(1)
        if row["resize"]:
            logger.info(f"Resizing image for {row['real_name']} to 512x512")
            img_data = resize_image(img_data)
        cast_dict = {
            "Comments": row["comments"],
            "Compressed": False,
            "Image": img_data,
            "Name": row["real_name"],
            "RoleName": row["character"],
            "Scaled": False,
            "Channel": row["channel"],
            "Version": 1,
        }
        wavetool_castlist.append(cast_dict)
    return wavetool_castlist
