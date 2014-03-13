#!/usr/bin/env python3

import argparse
import itertools as it
import sys
import csr

def normalize(l, lower, width):
	minimum= min(l)
	maximum= max(l)
	d= (maximum - minimum) / width
	l[:]= [(v - minimum) / d + lower for v in l]

def doit(input_file, output_file, columns, delimiter, wants_negative_one, has_header):
	# Read the entire input, accounting for the header, if any.
	if has_header:
		header= next(input_file)
	data= tuple(line.rstrip().split(delimiter) for line in input_file)
	if not data:
		return

	# Set the lower bound and width, if necessary.
	lower= -1.0 if wants_negative_one else 0.0
	width= 1.0 - lower

	# Determine desired column indices.
	indices= csr.parse(columns, true) if columns else tuple(range(len(data[0])))

	# Transpose the data into rows.
	data= list(zip(*data))

	# Normalize the desired columns, now in rows.
	for i in indices:
		data[i]= list(map(float, data[i]))
		normalize(data[i], lower, width)

	# Transpose the data back into columns.
	data= list(zip(*data))

	if has_header:
		print(header, end="", file=output_file)
	for row in data:
		print(*row, sep=delimiter, file=output_file)

if __name__ == "__main__":
	if "--test" in sys.argv:
		print("testing", file=sys.stderr)
		doit(["1 2 3","2 4 8","3 9 27"], sys.stdout, None, None, False, False)
		print("testing", file=sys.stderr)
		doit(["1,2,3","2,4,8","3,9,27"], sys.stdout, None, ',', False, False)
		print("testing", file=sys.stderr)
		doit(["A,1,2,3","B,2,4,8","C,3,9,27"], sys.stdout, "2-4", ',', False, False)
		print("testing", file=sys.stderr)
		doit(["A,1,2,3","B,2,4,8","C,3,9,27"], sys.stdout, "2-4", ',', True, False)
		print("testing", file=sys.stderr)
		doit(iter(["T,X,Y,Z\n", "A,1,2,3","B,2,4,8","C,3,9,27"]), sys.stdout, "2-4", ',', True, True)
		exit(0)
	parser= argparse.ArgumentParser(description="""Normalizes data in all or
		selected columns.""", epilog="""Selected columns must be numeric.  The
		upper bound is always 1.""")
	parser.add_argument("-d", "--delimiter", metavar="C",
		help="column delimiter character (default whitespace)")
	parser.add_argument("-n", "--negative-one", action="store_true",
		help="use -1 as the lower bound")
	parser.add_argument("-s", "--skip-header", action="store_true",
		help="skip the first row of data")
	parser.add_argument("columns", nargs='?',
		help="comma-delimited ranges of column numbers (default all)")
	parser.add_argument("input_file", nargs='?',
		type=argparse.FileType('r'), default=sys.stdin)
	parser.add_argument("output_file", nargs='?',
		type=argparse.FileType('w'), default=sys.stdout)
	args= parser.parse_args()
	doit(args.input_file, args.output_file, args.columns, args.delimiter, args.negative_one, args.skip_header)
