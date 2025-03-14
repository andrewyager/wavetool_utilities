import plistlib
import os
import sys
import pathlib
import traceback
import re
import requests
from util import crop_image, resize_image, import_castlist, build_castlist

"""
This script converts a CSV of a cast list with optional comments and images
into a .pla file that can be imported into WaveTool 3.
"""


def create_wavetool_castlist(wavetool_castlist, output_file, castlist_path):
    # wavetool_castlist is already built.
    plistlib.dump(wavetool_castlist, output_file)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python make_players.py <castlist.csv> <output.pla>")
        sys.exit(1)
    castlist_file = sys.argv[1]
    output_file = sys.argv[2]
    castlist = import_castlist(castlist_file)
    castlist_path = pathlib.Path(castlist_file).parent.resolve()
    # Build the processed cast list array once.
    wavetool_castlist = build_castlist(castlist, castlist_path)
    if os.path.isfile(output_file):
        overwrite = input("Output file already exists. Overwrite? (y/n): ")
        if overwrite.lower() != "y":
            sys.exit(0)
    try:
        with open(output_file, "wb") as out_fp:
            create_wavetool_castlist(wavetool_castlist, out_fp, castlist_path)
    except IOError:
        print("Could not open file: " + output_file)
        traceback.print_exc()
        sys.exit(1)
