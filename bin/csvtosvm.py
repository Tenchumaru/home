#!/usr/bin/env python3

import argparse
import io
import sys

def doit(input_file, output_file, ignore_first_line, target_column, ndigits):
  from quoted_line import parse as parse_line
  target_index = target_column - 1 if target_column >= 0 else target_column
  fmt= "%%.%dg" % ndigits
  if ignore_first_line:
    next(input_file)
    line_offset = 2
  else:
    line_offset = 1
  bad_data = set()
  for line_index, line in enumerate(input_file):
    if ',' in line:
      parts = parse_line(line, ',')
      if target_index < 0:
        target_index = len(parts) - 1
      output_line = parts[target_index]
      parts = parts[:target_index] + parts[target_index + 1:]
      for i, part in enumerate(s.strip() for s in parts):
        try:
          value= fmt % float(part)
          if value != "0":
            output_line += " {}:{}".format(i + 1, value)
        except ValueError:
          if len(bad_data) < 33:
            bad_data.add(line_index + line_offset)
          elif len(bad_data) == 33:
            bad_data.add("...")
      print(output_line, file=output_file)
    else:
      print(file=output_file)
  if bad_data:
    l= sorted(bad_data, key=lambda e: float("inf" if e == "..." else e))
    print("warning:  bad data in lines " + ", ".join(l), file=sys.stderr)
  return not bad_data

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="""Converts CSV data to LIBSVM
    data.""", epilog="""You may specify either a positive or negative target
    column.""")
  parser.add_argument("-i", "--ignore-first-line", action="store_true",
    help="ignore the first line")
  parser.add_argument("-p", "--precision", default=7, type=int,
    help="number of significant figures (default %(default)s)")
  parser.add_argument("-t", "--target", type=int, default=0,
    help="specify the column containing the target (default last column)")
  parser.add_argument("input_file", nargs="?",
    type=argparse.FileType("r"), default=sys.stdin,
    help="input CSV file (default standard input)")
  parser.add_argument("output_file", nargs="?",
    type=argparse.FileType("w"), default=sys.stdout,
    help="output SVM file (default standard output)")
  args = parser.parse_args()
  if not doit(args.input_file, args.output_file, args.ignore_first_line, args.target, args.precision):
    exit(1)
