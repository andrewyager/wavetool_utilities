import csv
from io import BytesIO
from PIL import Image as PILImage
import face_recognition


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

    # Check if image_buffer is valid
    if not image_buffer:
        print("Debug: Empty image buffer.")
        return image_buffer

    # Try opening the image with Pillow
    try:
        pil_image = PILImage.open(BytesIO(image_buffer))
        print("Debug: Successfully opened image. Size:", pil_image.size)
    except Exception as e:
        print("Debug: Could not open image from buffer. Error:", e)
        return image_buffer

    # Convert image to array for face detection
    try:
        image_array = face_recognition.load_image_file(BytesIO(image_buffer))
    except Exception as e:
        print("Debug: face_recognition.load_image_file failed. Error:", e)
        return image_buffer

    # Attempt to locate faces using the CNN model
    try:
        face_locations = face_recognition.face_locations(
            image_array, number_of_times_to_upsample=0, model="cnn"
        )
        print("Debug: Detected face locations:", face_locations)
    except RuntimeError as e:
        print("Debug: RuntimeError in face_recognition.face_locations:", e)
        return image_buffer

    # If no faces found, skip cropping
    if not face_locations:
        print("Debug: No faces found in image. Skipping crop.")
        new_buffer = BytesIO()
        pil_image.save(new_buffer, "JPEG")
        return new_buffer.getvalue()

    # Use the first detected face
    top, right, bottom, left = face_locations[0]
    face_width = right - left
    face_height = bottom - top

    # Expand the bounding box by 50%
    left = max(0, left - (face_width / 2))
    right = min(pil_image.width, right + (face_width / 2))
    top = max(0, top - (face_height / 2))
    bottom = min(pil_image.height, bottom + (face_height / 2))
    print(
        f"Debug: Cropping image with box coordinates: left={left}, top={top}, right={right}, bottom={bottom}"
    )

    cropped = pil_image.crop((left, top, right, bottom))
    if cropped.mode == "RGBA":
        cropped = cropped.convert("RGB")
    new_buffer = BytesIO()
    cropped.save(new_buffer, "JPEG")
    return new_buffer.getvalue()


def resize_image(image_buffer):
    """
    Resize an image so that its longest side is 512 pixels.
    Returns a JPEG image buffer.
    """
    image = PILImage.open(BytesIO(image_buffer))
    image.thumbnail((512, 512))
    new_buffer = BytesIO()
    image.save(new_buffer, "JPEG")
    return new_buffer.getvalue()
