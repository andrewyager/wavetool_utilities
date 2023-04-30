# WaveTool Utility Libraries

WaveTool is an amaizng tool. This set of helpers are designed to make working
with it a little more awesome.

## WaveTool v3 Player File Creator

If you love using WaveTool, but you have large cast lists, you
might find the process of importing large cast lists (particularly with
multiple players for roles) tedious.

This tool takes a CSV file of your cast and creates a WaveTool player
file for you.

### Import Format

The first row should have the headings "Character" and "Real Name" in any
order.

You can optionally specify a "Comments" and "Image" field which will populate
the "Comments" field in Wavetool.

The "Image" can be either a URL or a path on the local file system. Internet
paths are assumed to start with http or https. Please note that WaveTool will
accept JPG, PNG and TIFF file formats.

An example file "example.csv" is provided.

### Using the Importer

To use the utility, run the following command:

	python3 src/make_players.py <input_file> <output_file>

for example:

	python3 src/make_layers.py example.csv players.pla

## WSM to IP List File Creator

WaveTool 3 does not support discovery of Sennheiser wireless Devices within the
software, and expects you to know the IP address of all your Sennheiser transmitters.

Unfortunately this can be quite frustrating if you have a dynamic environment
where IP addresses can change from event to event.

This tool allows you to discover your hardware in WSM, save a configuration file
and then create a Wireless IP List (.wip) file for WaveTool which you can import
from the Wireless IP Device List window.

### Using the converter

To use the utility, run the following command:

	python3 src/wsm_to_ip_list.py <input_file.wsm> <output_file.wip>

for example:

	python3 src/wsm_to_ip_list.py ~/Documents/Configuration/example.wsm example.wip


## System Requirements

* Python 3.9 or higher
* WaveTool 3
* Python requests
* BeautifulSoup 4
* lxml

### Installation

We recommend creating a virtualenv. Download or clone the repository and then run

	git clone https://github.com/andrewyager/wavetool_utilities.git
	cd wavetool_players_creator
	virtualenv .
	source bin/activate
	pip install -r requirements.txt

This will get a copy of this repository, set up a local Python 3.9 environment
and then install the rqeuired dependencies. You can then run the utility as
is documented above.

Author: Andrew Yager <andrew@redglobe.au>

