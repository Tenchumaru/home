#!/usr/bin/env python3

import argparse
import itertools as it
import numpy as np
import scipy.optimize as sop
import sys

def as_bools(*t):
	if len(t) == 1 and "__iter__" in dir(t[0]):
		return as_bools(*t[0])
	else:
		return tuple(i in t for i in range(max(t) + 1))

class Model:
	def __repr__(self):
		return " ".join(map(str, self.theta.flat))

	def apply(self, x):
		# Add a bias column to x and multiply it by the model.
		x1= np.hstack((np.ones((x.shape[0], 1)), x))
		return np.dot(x1, self.theta)

class MinimizedModel(Model):
	def __init__(self, x, y, l, m, s):
		# Add a bias column to x and minimize a regularized cost function
		# of x onto y.
		def sigmoid(x, theta):
			return 1 / (1 + np.exp(-np.dot(x, theta)))
		def costFn(theta, x, y, l):
			p= np.dot(x, theta)
			q= np.log(1 + np.exp(p))
			cost= -np.sum(y * (p - q) + (y - 1) * q)
			theta2= theta[1:]
			cost += l / 2 * np.dot(theta2, theta2)
			return cost
		def gradFn(theta, x, y, l):
			grad= np.dot(x.T, sigmoid(x, theta) - y)
			theta2= theta[1:]
			grad[1:] += l * theta2
			return grad
		x1= np.hstack((np.ones((x.shape[0], 1)), x))
		initial_theta= np.zeros((x1.shape[1]))
		theta= sop.fmin_bfgs(costFn, initial_theta, gradFn, (x1, y, l), disp=0)
#		theta= sop.fmin(costFn, initial_theta, (x1, y, l), disp=0)
		theta[0] -= np.sum(theta[1:] * m / s)
		theta[1:] /= s
		self.theta= theta

def doit(input_file, output_file, regularization, wants_normalization):
	# Read the entire file.
	data= tuple(tuple(map(float, line.split(','))) for line in input_file)
	if len(data) == 0:
		print("no data", file=sys.stderr)
		return

	# Create X and Y indices.  Assume the last column contains the output and
	# the rest contain the inputs.
	y_index= len(data[0]) - 1
	x_indices= tuple(range(y_index))

	# Create and print the model parameters, normalizing the data if requested.
	data= np.array(data)
	x= np.compress(as_bools(x_indices), data, 1)
	mu= list(it.repeat(0.0, x.shape[1]))
	sigma= list(it.repeat(1.0, x.shape[1]))
	if wants_normalization:
		for i in range(x.shape[1]):
			mu[i]= np.mean(x[:,i])
			sigma[i]= np.std(x[:,i])
			if sigma[i] == 0.0:
				sigma[i]= 1.0
			x[:,i]= (x[:,i] - mu[i]) / sigma[i]
	y= np.compress(as_bools(y_index), data, 1).squeeze()
	model= MinimizedModel(x, y, regularization, mu, sigma)
	print(model, file=output_file)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="""Creates logistic regression
		model parameters.""", epilog="""The output variable must be in the last
		column of the input.""")
	parser.add_argument("-n", "--normalize", action="store_true",
		help="normalize the inputs and output model")
	parser.add_argument("regularization", type=float)
	parser.add_argument("input_file", nargs="?",
		type=argparse.FileType('r'), default=sys.stdin,
		help="the input data file")
	parser.add_argument("output_file", nargs="?",
		type=argparse.FileType('w'), default=sys.stdout,
		help="the output data file")
	args = parser.parse_args()
	doit(args.input_file, args.output_file, args.regularization, args.normalize)
