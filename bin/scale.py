#!/usr/bin/env python3

import argparse
import math
import sys
import tempfile

nan= float("NaN")

class MinMax:
  def __init__(self, value):
    self.wants_clamping= False
    if ' ' in value:
      self.is_restoring= True
      parts= value.strip().split()
      self.minimum, self.maximum, self.middle= map(float, parts)
      self.divisor= self.maximum - self.minimum
    else:
      self.is_restoring= False
      self.divisor= .0
      self.middle= .5
      try:
        value= value.strip()
        self.minimum= self.maximum= float(value)
      except ValueError as ex:
        # Ignore non-values.
        if value == '' or value == 'None':
          self.minimum= self.maximum= nan
        else:
          raise ex

  def add(self, value):
    if self.is_restoring:
      raise Exception("cannot add a value when restoring")
    try:
      value= value.strip()
      value= float(value)
    except ValueError as ex:
      # Ignore non-values.
      if value == '' or value == 'None':
        return
      else:
        raise ex
    self.minimum= min(value, self.minimum)
    self.maximum= max(value, self.maximum)
    self.divisor= self.maximum - self.minimum
    if math.isnan(self.divisor):
      self.divisor= .0

  def __repr__(self):
    return "{} {} {}".format(self.minimum, self.maximum, self.middle)

  def adjust(self, value):
    try:
      value= value.strip()
      result= (float(value) - self.minimum) / self.divisor if self.divisor else self.middle
      if self.wants_clamping:
        result= min(max(0 if self.middle else -1, result), 1)
      return result
    except ValueError as ex:
      if value == '' or value == 'None':
        return self.middle
      else:
        raise ex

  def ignore(self):
    if self.is_restoring:
      raise Exception("cannot ignore when restoring")
    self.minimum= self.maximum= self.divisor= 0

  def use_clamping(self):
    if not self.is_restoring:
      raise Exception("cannot clamp when saving")
    self.wants_clamping= True

  def use_negative_one(self):
    if self.is_restoring:
      raise Exception("cannot change lower bound when restoring")
    self.middle= .0
    self.divisor /= 2
    self.minimum= self.maximum - self.divisor

class MinMaxDict:
  def __init__(self):
    self.d= {}

  def __contains__(self, key):
    return int(key) in self.d

  def __getitem__(self, key):
    return self.d[int(key)]

  def __iter__(self):
    return iter(self.d)

  def ignore(self, columns_to_ignore):
    for k in columns_to_ignore:
      self.d[k].ignore()

  def update(self, key, value):
    key= int(key)
    if key in self.d:
      self.d[key].add(value)
    else:
      self.d[key]= MinMax(value)

  def use_negative_one(self):
    for v in self.d.values():
      v.use_negative_one()

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

def normalize(minmax_dict, input_file, output_file):
  for line in input_file:
    if ',' in line:
      parts= line.split(',')
      g= ("%g" % minmax_dict[k].adjust(v) for k, v in enumerate(parts))
      print(*g, sep=",", file=output_file)
    else:
      print(file=output_file)

def save(settings_file, input_file, output_file, columns_to_ignore, using_negative_one):
  import csr
  minmax_dict= MinMaxDict()
  input_file, input_handle= make_seekable(input_file)
  for k, v in read_pairs(input_file):
    minmax_dict.update(k, v)
  if using_negative_one:
    minmax_dict.use_negative_one()
  columns_to_ignore= csr.parse(columns_to_ignore, as_index=True) if columns_to_ignore else ()
  minmax_dict.ignore(columns_to_ignore)
  for k in minmax_dict:
    print(k, minmax_dict[k], file=settings_file)
  input_file.seek(0)
  normalize(minmax_dict, input_file, output_file)

def restore(settings_file, input_file, output_file, wants_clamping):
  g= (line.split(None, 1) for line in settings_file)
  minmax_dict= {int(p[0]): MinMax(p[1]) for p in g}
  if wants_clamping:
    for v in minmax_dict.values():
      v.use_clamping()
  normalize(minmax_dict, input_file, output_file)

if __name__ == "__main__":
  parser= argparse.ArgumentParser(description="""Scales a CSV dataset so all
    features are in [0, 1].""", epilog="""You must specify either save (-s,
    --save) or restore (-r, --restore).  The restore operation ignores the
    negative-one and ignore options.  The save operation stores information
    about those options in the settings file.  Only the restore operation uses
    the clamp option.""")
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
    save(args.save, args.input_file, args.output_file, args.ignore, args.negative_one)
  elif args.restore and not args.save:
    restore(args.restore, args.input_file, args.output_file, args.clamp)
  else:
    parser.parse_args(["-h"])
