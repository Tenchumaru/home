#!/usr/bin/env python3

def parse(line, delimiter):
  line = line.strip()
  if '"' not in delimiter and '"' in line:
    in_quotes = False
    parts = []
    part = ""
    for ch in line:
      if in_quotes:
        if ch == '"':
          in_quotes = False
        else:
          part += ch
      else:
        if ch == '"':
          in_quotes = True
        elif ch == delimiter:
          parts.append(part)
          part = ""
        else:
          part += ch
    parts.append(part)
    return parts
  else:
    return line.split(delimiter)
