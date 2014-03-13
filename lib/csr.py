import itertools as it

def parse(arg, as_index):
	"""Parses a string containing a comma-delimited list of ranges into a tuple
      of integers."""
	a= 1 if as_index else 0
	b= 1 - a
	def as_range(s):
		parts= s.split("-")
		return range(int(parts[0]) - a, int(parts[-1]) + b)
	return tuple(it.chain(*map(as_range, arg.split(","))))
