= WaveTool v3 Player File Creator =

If you love using WaveTool, but you have large cast lists, you
might find the process of importing large cast lists (particularly with
multiple players for roles) tedious.

This tool takes a CSV file of your cast and creates a WaveTool player
file for you.

The first row should have the headings "Character" and "Real Name" in any
order.

To use the utility, run the following command:

	`python3 src/make_players.py <input_file> <output_file>`

for example:

	`python3 src/make_layers.py example.csv players.pla`

Requirements:

* Python 3.9 or higher
* WaveTool 3

Author: Andrew Yager <andrew@redglobe.au>

