#!/usr/bin/env python3

import argparse
from atexit import register as on_exit
import os
from signal import signal, SIGTERM
import sys

class DaemonParameters:
  def __init__(self):
    self.input_file_path= "/dev/null"
    self.output_file_path= "/dev/null"
    self.error_file_path= "/dev/null"
    self.working_directory= "/"
    self.file_mode_mask= 0
    self.sigterm_fn= None

# https://en.wikipedia.org/wiki/Daemon_(computing)#Creation
def make_daemon(pid_file_path, parameters=None):
  parameters= parameters or DaemonParameters()

  if os.path.exists(pid_file_path):
    raise RuntimeError("Daemon already running (or crashed)")

  # Fork to separate from and exit the parent process.
  if os.fork() > 0:
    sys.exit(0)

  # Become a session (and process group) leader.  This will cause the child
  # process to dissociate from the parent's terminal.
  os.setsid()

  # Set the working directory and file mode mask.
  os.chdir(parameters.working_directory)
  os.umask(parameters.file_mode_mask)

  # Fork again to cede session and process group leadership.  This ensures the
  # grandchild process cannot acquire a terminal.
  if os.fork() > 0:
    sys.exit(0)

  # Flush the output streams.
  sys.stdout.flush()
  sys.stderr.flush()

  # Replace the standard stream file descriptors.
  with open(parameters.input_file_path, "rb", 0) as fin:
    os.dup2(fin.fileno(), sys.stdin.fileno())
  with open(parameters.output_file_path, "ab", 0) as fout:
    os.dup2(fout.fileno(), sys.stdout.fileno())
  with open(parameters.error_file_path, "ab", 0) as ferr:
    os.dup2(ferr.fileno(), sys.stderr.fileno())

  # Write the grandchild (daemon) process's ID to the PID file.
  with open(pid_file_path, "w") as fout:
    print(os.getpid(), file=fout)

  # Remove the PID file upon exit.
  on_exit(lambda: os.remove(pid_file_path))

  # Configure a handler for the termination signal to ensure proper clean-up.
  def sigterm_handler(signo, frame):
    parameters.sigterm_fn and parameters.sigterm_fn()
    sys.exit(3)
  signal(SIGTERM, sigterm_handler)

def start(pid_file_path, fn, args, parameters=None):
  make_daemon(pid_file_path, parameters)
  fn(args) if args else fn()

def stop(pid_file_path):
  if os.path.exists(pid_file_path):
    with open(pid_file_path) as fin:
      os.kill(int(fin.read()), SIGTERM)
      return True

def main(daemon_name, fn, parameters, argparser=None):
  parser= argparser or argparse.ArgumentParser(description="Control the {} daemon.".format(daemon_name))
  parser.add_argument("action", choices=["start", "stop"],
      help="start or stop the service")
  args= parser.parse_args()
  if args.action == "start":
    start(pid_file_path, fn, argparser, parameters)
  elif not stop(pid_file_path):
    print("Daemon {} not running".format(daemon_name), file=sys.stderr)
    sys.exit(1)
