#!/usr/bin/python

import sys
import optparse
import re

def opt_get():
	parser = optparse.OptionParser()
	parser.add_option('-i', '--INPUT', dest = "in_file", action = "store")
	parser.add_option('-g', '--GFF_FILE', dest = "gff", action = "store")
	parser.add_option('-o', '--OUTPUT', dest = "out_file", action = "store")
	(options, args) = parser.parse_args()
	return(options)

## Load GFF into memory only selecting mRNA field
## Storing start and stop coordinates as a tuple dictionary key with the ATnG as value
## Skipping isoforms
def gff_read(gff_file, field):
	print "Reading GFF file."
	print "Searching for %s" % field
	gff_out = {}
	records_found = 0 
	parents = {}
	while True:
		line = gff_file.readline()
		if not line:
			print "Found %s %s records in GFF" % (field, records_found)
			return(gff_out)
		fields = line.split('\t')
		if fields[2] == field:
			start = fields[3]
			stop = fields[4]
			parent = re.sub("Parent=", "", fields[8].split(';')[1])
			if parent in parents:
				continue
			else:
				records_found += 1
				parents[parent] = 1
				gff[(start, stop)] = parent



## Start reading VCF files

for start, stop in gff_out: