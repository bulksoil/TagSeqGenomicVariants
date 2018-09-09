#!/usr/bin/install

import sys
import optparse
import os
import re

def opt_get():
	parser = optparse.OptionParser()
	parser.add_option('-i', '--INPUT', dest = "in_file", action = "store")
	parser.add_option('-n', '--nMin', dest = "n", action = "store")
	parser.add_option('-o', '--OUTPUT', dest = "out_file", action = "store")
	parser.add_option('-c', '--COMP', dest = "compression_type", action = "store", default = "none")
	(options, args) = parser.parse_args()
	return(options)

def fq_read(fh):

	fq_data = {}
	fq_data['header'] = fh.readline()
	fq_data['seq'] = fh.readline().rstrip("\n")
	fq_data['spacer'] = fh.readline()
	fq_data['qual'] = fh.readline().rstrip("\n")

	if fq_data['header']:
		return fq_data
	else:
		return("none")

def pA_find(seq):
	place = seq.find('AAAA')
	return(place)

def main():
	options = opt_get()
	in_file = options.in_file
	out_file = options.out_file
	n = int(options.n)
	compression_type = options.compression_type

	if compression_type not in ["none", "b", "g"]:
		sys.exit("Wrong compression type used: valid options are 'none', 'b' and 'g'.")

	if compression_type == "b":
		from bz2 import BZ2File as bzopen
		fh = bzopen(in_file, 'r')
	if compression_type == "g":
		import gzip
		fh = gzip.open(in_file, 'r')
	else:
		fh = open(in_file, 'r')

	out = open(out_file, 'w')

	iters = 0
	lost = 0
	while True:
		fq_data = fq_read(fh)

		if fq_data == "none":
			print "Processed " + str(iters) + " reads."
			print "Removed " + str(lost) + " reads (" + str(float(lost) / float(iters) * 100) + "%)"
			break

		iters += 1
		cut_place = pA_find(fq_data['seq'])
		if cut_place == 0 or len(fq_data['seq'][:cut_place]) < n:
			lost += 1
			continue

		out.write(fq_data['header'])
		out.write(fq_data['seq'][:cut_place] + "\n")
		out.write(fq_data['spacer'])
		out.write(fq_data['qual'][:cut_place] + "\n")

		if iters % 1000 == 0:
			sys.stdout.write('%s\r' % iters)
    		sys.stdout.flush()

main()