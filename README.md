# WaveTool v3 Player File Creator

If you love using WaveTool, but you have large cast lists, you
might find the process of importing large cast lists (particularly with
multiple players for roles) tedious.

This tool takes a CSV file of your cast and creates a WaveTool player
file for you.

## Import Format

The first row should have the headings "Character" and "Real Name" in any
order.

You can optionally specify a "Comments" and "Image" field which will populate
the "Comments" field in Wavetool.

The "Image" can be either a URL or a path on the local file system. Internet
paths are assumed to start with http or https. Please note that WaveTool will
accept JPG, PNG and TIFF file formats.

An example file "example.csv" is provided.

## Using the Importer

To use the utility, run the following command:

	python3 src/make_players.py <input_file> <output_file>

for example:

	python3 src/make_layers.py example.csv players.pla

## System Requirements

* Python 3.9 or higher
* WaveTool 3
* Python requests

## Installation

We recommend creating a virtualenv. Download or clone the repository and then run

	git clone https://github.com/andrewyager/wavetool_players_creator.git
	cd wavetool_players_creator
	virtualenv .
	source bin/activate
	pip install -r requirements.txt

This will get a copy of this repository, set up a local Python 3.9 environment
and then install the rqeuired dependencies. You can then run the utility as
is documented above.

Author: Andrew Yager <andrew@redglobe.au>

