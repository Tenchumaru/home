#!/usr/bin/env python3

import argparse
import io
import itertools
import sys

def parse_line(line, column_count):
	line = line.strip()
	parts = line.split()
	target = parts[0]
	features = parts[1:]
	if column_count:
		if column_count < len(parts):
			return []
		values = list(itertools.repeat(0, column_count))
	elif features:
		feature_count = max(int(p.split(':')[0]) for p in features)
		values = list(itertools.repeat(0, feature_count + 1))
	else:
		values = [0]
	for feature in features:
		column, value = feature.split(':', 1)
		values[int(column) - 1] = value
	values[-1] = target
	return values

def doit(input_file, output_file, feature_count):
	column_count = feature_count + 1
	has_bad_data = []
	for line_index, line in enumerate(input_file):
		parts = parse_line(line, column_count)
		if column_count == 0:
			column_count = len(parts)
			print("using", column_count - 1, "as feature count", file=sys.stderr)
		if column_count == len(parts):
			print(*parts, sep=',', file=output_file)
		elif len(has_bad_data) < 22:
			has_bad_data.append(line_index + 1)
		elif len(has_bad_data) == 22:
			has_bad_data.append("...")
	if has_bad_data:
		print("warning:  feature count not", column_count - 1, "in lines", has_bad_data, file=sys.stderr)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="Creates CSV data from LIBSVM data.",
		epilog="The target is in the last column.")
	parser.add_argument("-f", "--feature-count", type=int, default=-1,
		help="the number of features (if the first row doesn't contain all features)")
	parser.add_argument("-p", "--precision", default=7, type=int, help="number of digits after the decimal (default %(default)s)")
	parser.add_argument("input_file", nargs="?", type=argparse.FileType('r'), default=sys.stdin)
	parser.add_argument("output_file", nargs="?", type=argparse.FileType('w'), default=sys.stdout)
	args = parser.parse_args()
	doit(args.input_file, args.output_file, args.feature_count)
