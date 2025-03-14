import os
import sys
import pathlib
import traceback
import re
import requests
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from util import crop_image, resize_image, import_castlist, build_castlist

"""
This script converts a CSV of a cast list with optional comments and images
into a PDF of mic cards.
"""


def create_mic_cards(wavetool_castlist, output_file, castlist_path):
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
    if len(sys.argv) < 3:
        print("Usage: python mic_cards.py <castlist.csv> <output.pdf>")
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
            create_mic_cards(wavetool_castlist, out_fp, castlist_path)
    except IOError:
        print("Could not open file: " + output_file)
        traceback.print_exc()
        sys.exit(1)
