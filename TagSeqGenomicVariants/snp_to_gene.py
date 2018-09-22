#!/usr/bin/python

import sys
import optparse
import re

def opt_get():
	parser = optparse.OptionParser()
	parser.add_option('-i', '--INPUT', dest = "vcf", action = "store")
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
			chrom = re.sub("Chr", "", fields[0])
			if chrom == "C":
				chrom = "chloroplast"
			if chrom == "M":
				chrom = "mitochondria"
			start = int(fields[3])
			stop = int(fields[4])
			parent = re.sub("Parent=", "", fields[8].split(';')[1])

			#print "%s %s %s %s" % (chrom, start, stop, parent)
			if parent in parents:
				continue
			if not chrom in gff_out:
				gff_out[chrom] = {}
			else:
				records_found += 1
				parents[parent] = 1
				gff_out[chrom][(start, stop)] = parent



## Start reading VCF files
def vcf_read(vcf, gff, out):

	current_chrom = 0
	while True:
		line = vcf.readline()
		if not line:
			return()
		if line.startswith('##'):
			continue
		if line.startswith('#'):
			out.write("Gene\t%s" % re.sub("#", "", line))
			continue
		fields = line.split('\t')
		chrom = fields[0]
		position = int(fields[1])
		if chrom != current_chrom:
			current_chrom = chrom
			print "Changing dictionary to chromosome %s" % chrom
			temp_dict = gff[chrom]
		for start, stop in temp_dict.keys():
			if start <= position <= stop:
				parent = temp_dict[(start, stop)]
				out.write("%s\t%s" % (parent, line))
				#print "%s\t%s\t%s\t%s" % (str(chrom), str(position), str(start), str(stop), parent)


def main():
	options = opt_get()
	gff_f = options.gff
	vcf_f = options.vcf
	out_f = options.out_file

	gff_fh = open(gff_f, 'r')
	vcf_fh = open(vcf_f, 'r')
	out_fh = open(out_f, 'w')

	gff = gff_read(gff_fh, 'mRNA')
	vcf_read(vcf_fh, gff, out_fh)

main()







