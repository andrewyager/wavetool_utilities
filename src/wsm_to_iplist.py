import os
from bs4 import BeautifulSoup
import plistlib

"""

This is a utility to take a Sennheiser WSM configuration file and create a WaveTool Wireless
IP list.

While WaveTool auto discovers Shure hardware, they do not have this ability for Sennheiser.

Once you have located your devices in WSM, this will allow you to quickly import the IP
addresses into WaveTool as Sennheiser devices, reducing time and errors associated with
more complex setups.

"""


def wsm_to_wtip(source_file, output_file):
    ip_addresses = []
    with open(source_file, "r") as f:
        soup = BeautifulSoup(f, "xml")

        ip_fields = soup.find_all("IPAddress")

        for ip_field in ip_fields:
            ip_addresses.append([ip_field.text, 3])

    plistlib.dump(ip_addresses, open(output_file, "wb"))


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: wsm_to_wtip.py <source_file> <output_file>")
        sys.exit(1)

    source_file = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.isfile(source_file):
        print(f"Error: {source_file} is not a file")
        sys.exit(1)

    if os.path.isfile(output_file):
        overwrite = input(
            "Output file already exists. Do you want to overwrite? (y/n): "
        )
        if overwrite != "y":
            exit(0)

    wsm_to_wtip(source_file, output_file)
