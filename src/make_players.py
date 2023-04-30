import plistlib
import os
import csv
import sys
import pprint


def import_castlist(castlist_file):
    # Import castlist from CSV file
    castlist = []
    with open(castlist_file, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if "Real Name" not in row:
                real_name = ""
            else:
                real_name = row["Real Name"]
            if "Character" not in row:
                character = ""
            else:
                character = row["Character"]
            if real_name == "" and character == "":
                continue
            character = {"character": character, "real_name": real_name}
            castlist.append(character)
    return castlist


def create_wavetool_castlist(castlist, output_file):
    with open("defaultimage.tiff", "rb") as image:
        image = image.read()
    wavetool_castlist = []
    for row in castlist:
        cast_dict = dict(
            Comments="",
            Compressed=True,
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
        print("Output file already exists. Do you want to overwrite? (y/n)")
        overwrite = input()
        if overwrite != "y":
            exit(0)
    try:
        output_file_handler = open(output_file, "wb")
        create_wavetool_castlist(castlist, output_file_handler)
    except IOError:
        print("Could not open file: " + output_file)
        exit(1)
