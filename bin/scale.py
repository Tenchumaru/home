#!/usr/bin/env python3

import argparse
import sys
import tempfile
from collections import defaultdict
from math import erf, isnan, sqrt

nan= float("NaN")

def as_value(s):
  if s[0] == 'n':
    v= -float(s[1:])
  elif s[0] == 'p':
    v= float(s[1:])
  else:
    raise ValueError("unexpected value " + s)
  return .5 + .5 * erf(v / sqrt(2.))

class MinMax:
  def __init__(self, using_negative_one, using_standard_deviation):
    if type(using_negative_one) == str:
      parts= using_negative_one.split()
      self.m, self.b, self.lower_bound, self.upper_bound= map(float, parts)
      self.wants_clamping= using_standard_deviation
    else:
      self.upper_bound= 1.
      self.lower_bound= -1. if using_negative_one else .0
      self.using_standard_deviation= using_standard_deviation
      self.wants_clamping= False
      if using_standard_deviation:
        self.k= 0
        self.a= self.q= .0
      else:
        self.minimum= self.maximum= nan
    self.middle= (self.upper_bound + self.lower_bound) / 2.

  def __str__(self):
    if self.using_standard_deviation and self.k != 0:
      sd= sqrt(self.q / self.k)
      self.minimum= self.a - sd
      self.maximum= self.a + sd
    if self.maximum == self.minimum or isnan(self.maximum) or isnan(self.minimum):
      self.m= .0
      self.b= (self.upper_bound - self.lower_bound) / 2.
    else:
      self.m= (self.upper_bound - self.lower_bound) / (self.maximum - self.minimum)
      self.b= self.upper_bound - self.m * self.maximum
    return '%g %g %g %g' % (self.m, self.b, self.lower_bound, self.upper_bound)

  def add(self, value):
    try:
      value= value.strip()
      value= float(value)
      if isnan(value):
        return
    except ValueError as ex:
      # Ignore non-values.
      if value == '' or value == 'None':
        return
      else:
        # If it's convertible, ignore it.
        as_value(value)
        return
      raise
    if self.using_standard_deviation:
      self.k += 1
      diff= value - self.a
      self.a += diff / self.k
      self.q += diff * (value - self.a)
    else:
      self.minimum= min(value, self.minimum)
      self.maximum= max(value, self.maximum)

  def adjust(self, value):
    try:
      value= value.strip()
      result= self.m * float(value) + self.b
      if self.wants_clamping:
        result= min(max(self.lower_bound, result), self.upper_bound)
    except ValueError as ex:
      if value == '' or value == 'None':
        result= self.middle
      else:
        result= as_value(value)
        if self.middle == .0:
          # Negative one is the lower bound.
          result= 2. * result - 1.
    return "%g" % round(result + 1e-9, 5) # Prevent negative zero.

class MinMaxIgnored:
  def __init__(self):
    pass

  def __str__(self):
    return ''

  def add(self, value):
    pass

  def adjust(self, value):
    return value

class MinMaxDict:
  def __init__(self, columns_to_ignore, using_negative_one, using_standard_deviation):
    self.d= {}
    self.columns_to_ignore= columns_to_ignore
    self.using_negative_one= using_negative_one
    self.using_standard_deviation= using_standard_deviation

  def __contains__(self, key):
    return key in self.d

  def __getitem__(self, key):
    value= self.d.get(key)
    if not value:
      self.d[key]= value= MinMaxIgnored() if key in self.columns_to_ignore else MinMax(self.using_negative_one, self.using_standard_deviation)
    return value

  def __iter__(self):
    return iter(self.d)

def make_seekable(input_file):
  # Assign the return value to a variable to prevent the garbage collector
  # from deleting the temporary file too soon.
  if input_file.seekable():
    return input_file, None
  t= tempfile.TemporaryFile()
  for line in input_file:
    t.write(line.encode())
  t.seek(0)
  return open(t.fileno()), t

def read_pairs(input_file):
  for line in input_file:
    for k, v in enumerate(line.split(',')):
      yield k, v

def normalize(min_max_dict, input_file, output_file):
  for line in input_file:
    if ',' in line:
      parts= line.split(',')
      g= (min_max_dict[k].adjust(v) for k, v in enumerate(parts))
      print(*g, sep=",", file=output_file)
    else:
      print(file=output_file)

def save(settings_file, input_file, output_file, columns_to_ignore, using_negative_one, using_standard_deviation):
  import csr
  columns_to_ignore= csr.parse(columns_to_ignore, as_index=True)
  min_max_dict= MinMaxDict(columns_to_ignore, using_negative_one, using_standard_deviation)
  input_file, input_handle= make_seekable(input_file)
  for k, v in read_pairs(input_file):
    min_max_dict[k].add(v)
  for k in min_max_dict:
    print(k, min_max_dict[k], sep=':', file=settings_file)
  input_file.seek(0)
  normalize(min_max_dict, input_file, output_file)

def restore(settings_file, input_file, output_file, wants_clamping):
  g= (line.rstrip().split(':') for line in settings_file)
  def make_min_max(s):
    return MinMax(s, wants_clamping) if s else MinMaxIgnored()
  min_max_dict= {int(p[0]): make_min_max(p[1]) for p in g}
  normalize(min_max_dict, input_file, output_file)

if __name__ == "__main__":
  parser= argparse.ArgumentParser(description="""Scales a CSV dataset so all
    values are in a specific range (default [0, 1]).""", epilog="""You must
    specify either save (-s, --save) or restore (-r, --restore).  The restore
    operation ignores the negative-one, standard-deviation, and ignore options.
    The save operation stores information about those options in the settings
    file.  Only the restore operation uses the clamp option.  Specifying the
    standard-deviation option results in output that may exceed the range.""")
  parser.add_argument("-s", "--save", metavar="settings_file",
    type=argparse.FileType('w'),
    help="the scaling parameter settings save file")
  parser.add_argument("-r", "--restore", metavar="settings_file",
    type=argparse.FileType('r'),
    help="the scaling parameter settings restore file")
  parser.add_argument("-c", "--clamp", action="store_true",
    help="ensure scaled values are within range")
  parser.add_argument("-n", "--negative-one", action="store_true",
    help="use -1 instead of 0 as the lower bound")
  parser.add_argument("-d", "--standard-deviation", action="store_true",
    help="use the standard deviation to determine the scaling")
  parser.add_argument("-i", "--ignore", metavar="COLUMNS", default="",
    help="a comma-delimited list of columns to not scale")
  parser.add_argument("input_file", nargs="?",
    type=argparse.FileType('r'), default=sys.stdin,
    help="the input data file (default standard input)")
  parser.add_argument("output_file", nargs="?",
    type=argparse.FileType('w'), default=sys.stdout,
    help="the scaled output data file (default standard output)")
  args= parser.parse_args()
  if args.save and not args.restore:
    save(args.save, args.input_file, args.output_file, args.ignore, args.negative_one, args.standard_deviation)
  elif args.restore and not args.save:
    restore(args.restore, args.input_file, args.output_file, args.clamp)
  else:
    parser.parse_args(["-h"])
