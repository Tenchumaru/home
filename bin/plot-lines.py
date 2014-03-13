#!/usr/bin/env python3

import argparse
import datetime
import itertools as it
import pygal
import sys

def doit(input_file, output_file, columns, delimiter, has_header, title, x_column):
	# Read the entire input, accounting for the header, if any.
	g= (line.rstrip().split(delimiter) for line in input_file)
	if has_header:
		header= next(g)
	data= tuple(g)
	if not data:
		return

	# Transpose the data into rows.
	data= list(zip(*data))
	if not has_header:
		header= tuple("F%d" % i for i in range(len(data)))

	# Determine the X column (now row) labels, if any.
	if x_column:
		x_labels= data[int(x_column) - 1]

	# Determine desired column (now row) indices.
	if columns:
		def as_index_range(s):
			parts= s.split('-')
			return range(int(parts[0]) - 1, int(parts[-1]))
		indices= tuple(it.chain(*map(as_index_range, columns.split(','))))
	else:
		indices= tuple(range(len(data[0])))

	# Convert the desired columns (now rows) of data into floats.
	def convert(row):
		return tuple(map(float, row))
	g= (data[i] for i in indices)
	data= tuple(map(convert, g))
	header= tuple(header[i] for i in indices)

	# Create the line chart.
	c= pygal.Line(show_dots=False)
	if title:
		c.title= title
	if x_column:
		c.x_labels= x_labels
	for i, row in enumerate(data):
		c.add(header[i], row)
	print(c.render().decode(), file=output_file)

if __name__ == "__main__":
	parser= argparse.ArgumentParser(description="Creates a line chart of data.")
	parser.add_argument("-d", "--delimiter", metavar="C",
		help="column delimiter character (default whitespace)")
	parser.add_argument("-l", "--legend", action="store_true",
		help="use the first line as the names in the legend")
	parser.add_argument("-t", "--title",
		help="title of the chart")
	parser.add_argument("-x", "--x-labels", metavar="N",
		help="column number of data containing labels for X axis")
	parser.add_argument("columns",
		help="comma-delimited ranges of column numbers to plot")
	parser.add_argument("input_file", nargs='?',
		type=argparse.FileType('r'), default=sys.stdin)
	parser.add_argument("output_file", nargs='?',
		type=argparse.FileType('w'), default=sys.stdout,
		help="output SVG file")
	args= parser.parse_args()
	doit(args.input_file, args.output_file, args.columns, args.delimiter, args.legend, args.title, args.x_labels)
