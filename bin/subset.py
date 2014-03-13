#!/usr/bin/env python3

import argparse
import random
import subprocess
import sys

def doit(subset_size, seed, input_file, output_file, unselected_file):
	if seed:
		random.seed(seed)
	line_count = int(subprocess.check_output(["wc", input_file.name]).decode().split()[0])
	sample_count= round(line_count * float(subset_size[:-1]) / 100) if subset_size[-1] == '%' else int(subset_size)
	sample_indices = set(random.sample(range(line_count), sample_count))
	for i, line in enumerate(input_file):
		if i in sample_indices:
			print(line.strip(), file=output_file)
		elif unselected_file:
			print(line.strip(), file=unselected_file)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Selects a random subset of a dataset in any line-oriented format.")
	parser.add_argument("-s", "--seed", type=int, help="the random seed")
	parser.add_argument("input_file", type=argparse.FileType('r'), help="the input data file")
	parser.add_argument("subset_size", help="the number of lines (or a percentage) to select")
	parser.add_argument("output_file", nargs="?", type=argparse.FileType('w'), default=sys.stdout, help="the selected data (default stdout)")
	parser.add_argument("unselected_file", nargs="?", type=argparse.FileType('w'), help="the rest of the input (default /dev/null)")
	args = parser.parse_args()
	doit(args.subset_size, args.seed, args.input_file, args.output_file, args.unselected_file)
