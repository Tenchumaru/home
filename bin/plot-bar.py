#!/usr/bin/env python3

import argparse
import itertools as it
import pygal
import sys

def as_parts(s):
  return s.strip().split(",")

def try_float(s):
  return float(s) if s else None

class Row:
  legend_column= None
  count= 0

  def __init__(self, parts):
    self.data= []
    Row.count += 1
    self.legend= str(Row.count)
    for i, s in enumerate(parts):
      if i == Row.legend_column:
        self.legend= s
      elif i in Row.column_indices:
        self.data.append(try_float(s))

def doit(input_file, output_file, wants_stacked, has_header, title, legend_column, columns, configuration):
  # Read the entire input.
  input_file= tuple(map(as_parts, input_file))
  if not len(input_file):
    print("no data", file=sys.stderr)
    return

  # If there is a header, read it for the title and X labels.
  x_labels= None
  first_row_index= 0
  if has_header:
    parts= input_file[0]
    first_row_index= 1
    if legend_column:
      Row.legend_column= int(legend_column) - 1
      if not title:
        title= parts[Row.legend_column]
    x_labels= tuple(s for i, s in enumerate(parts) if i != Row.legend_column)

  # Determine desired column indices.
  if columns:
    from csr import parse as parse_ranges
    Row.column_indices= parse_ranges(columns, as_index= True)
  else:
    Row.column_indices= tuple(range(len(input_file[0])))

  # Extract the desired columns from the input.
  data= tuple(map(Row, input_file[first_row_index:]))
  if len(data) == 0:
    print("no data", file=sys.stderr)
    return

  # Create the chart.
  chart_type= pygal.StackedBar if wants_stacked else pygal.Bar
  chart= chart_type(show_legend= len(data) != 1)
  if title:
    chart.title= title
  for row in data:
    chart.add(row.legend, row.data)
  if x_labels:
    chart.x_labels= x_labels
  if configuration:
    from ast import literal_eval
    configuration= literal_eval(configuration)
    for k, v in configuration.items():
      setattr(chart.config, k, v)
  result= chart.render()
  output_file.write(str(result, encoding="utf-8"))

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Plots data as a bar chart.",
    epilog="""If skipping the first line as a header, it is used to specify the
    title (in the legend column if not otherwise provided) and X labels.""")
  parser.add_argument("-k", "--stacked", action="store_true",
    help="create a stacked bar chart")
  parser.add_argument("-s", "--skip-header", action="store_true",
    help="skip the first line of the file")
  parser.add_argument("-c", "--columns",
    help="comma-delimited ranges of columns to plot (default all except the legend column)")
  parser.add_argument("-t", "--title",
    help="the title of the chart")
  parser.add_argument("-l", "--legend", type=int, metavar="N",
    help="the column number of the legend")
  parser.add_argument("-n", "--configuration",
    help="additional configuration for the chart")
  parser.add_argument("input_file", nargs="?",
    type=argparse.FileType('r'), default=sys.stdin,
    help="the input CSV file (default standard input)")
  parser.add_argument("output_file", nargs="?",
    type=argparse.FileType('w'), default=sys.stdout,
    help="the output SVG file (default standard output)")
  args = parser.parse_args()
  doit(args.input_file, args.output_file, args.stacked, args.skip_header, args.title, args.legend, args.columns, args.configuration)
