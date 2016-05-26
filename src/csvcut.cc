// g++ -std=c++11 -o ../bin/csvcut -O2 csvcut.cc

#include <algorithm>
#include <fstream>
#include <iostream>
#include <istream>
#include <limits>
#include <set>
#include <string>
#include <vector>
#include <cstring>
#include <unistd.h>

static int usage(char const* prog) {
	std::cerr << "print selected columns to standard output" << std::endl;
	std::cerr << std::endl;
	std::cerr << "usage: " << prog << " [-h] -(c|K) columns [input.csv]" << std::endl;
	std::cerr << std::endl;
	std::cerr << "\t-c\tcomma-separated list of 1-based column ranges to print" << std::endl;
	std::cerr << "\t-K\tcomma-separated list of 0-based column ranges to print" << std::endl;
	return 2;
}

static size_t all_begin = std::numeric_limits<size_t>::max();
static std::vector<int> column_vector;

static void parse_columns(char const* optarg, bool is_one_based) {
	if(all_begin < std::numeric_limits<size_t>::max() || !column_vector.empty()) {
		std::cerr << "provide column specification only once" << std::endl;
		exit(1);
	}
	std::set<int> column_set;
	enum class State { Initial, Left, Between, Right, } state = State::Initial;
	char ch;
	size_t left, value;
	char const* p = optarg;
	do {
		ch = *p++;
		switch(state) {
		case State::Initial:
			if(ch == '-') {
				// range open on left; assume first column
				left = is_one_based ? 1 : 0;
				state = State::Between;
			} else if(isdigit(ch)) {
				value = ch - '0';
				state = State::Left;
			} else if(ch == '\0' || ch == ',') {
				// ignore empty column specification
			} else {
				std::cerr << "invalid column specification \"" << optarg << '"' << std::endl;
				exit(1);
			}
			break;
		case State::Left:
			if(ch == '-') {
				left = value;
				state = State::Between;
			} else if(isdigit(ch)) {
				value *= 10;
				value += ch - '0';
			} else if(ch == ',') {
				column_set.insert(value);
				state = State::Initial;
			} else if(ch == '\0') {
				column_set.insert(value);
			} else {
				std::cerr << "invalid column specification \"" << optarg << '"' << std::endl;
				exit(1);
			}
			break;
		case State::Between:
			if(isdigit(ch)) {
				value = ch - '0';
				state = State::Right;
			} else if(ch == '\0' || ch == ',') {
				// range open on right
				all_begin = std::min(all_begin, left);
				state = State::Initial;
			} else {
				std::cerr << "invalid column specification \"" << optarg << '"' << std::endl;
				exit(1);
			}
			break;
		case State::Right:
			if(isdigit(ch)) {
				value *= 10;
				value += ch - '0';
			} else if(ch == '\0' || ch == ',') {
				for(size_t i = left; i <= value; ++i) {
					column_set.insert(i);
				}
				state = State::Initial;
			} else {
				std::cerr << "invalid column specification \"" << optarg << '"' << std::endl;
				exit(1);
			}
			break;
		}
	} while(ch);
	auto n= *std::max_element(column_set.begin(), column_set.end());
	column_vector.resize(is_one_based ? n : n + 1);
	for(auto& i : column_set) {
		column_vector[is_one_based ? i - 1 : i] = true;
	}
	if(all_begin < std::numeric_limits<size_t>::max()) {
		if(is_one_based) {
			--all_begin;
		}
		column_vector.resize(all_begin);
	}
	if(all_begin == column_vector.size() && std::all_of(column_vector.begin(), column_vector.end(), [](int i) { return !!i; })) {
		std::cerr << "invalid column specification \"" << optarg << '"' << std::endl;
		exit(1);
	}
}

static void csvcut(std::istream& sin) {
	std::string input, output;
	while(std::getline(sin, input)) {
		output.clear();
		size_t column_index = 0;
		bool is_in_quote = false, needs_comma = false, wants_output = !!column_vector[0];
		char const* p = nullptr;
		for(auto& ch : input) {
			if(ch == '"') {
				is_in_quote = !is_in_quote;
			} else if(!is_in_quote && ch == ',') {
				++column_index;
				if(column_index >= column_vector.size()) {
					if(column_index >= all_begin) {
						p = 1 + &ch;
					}
					break;
				}
				if(needs_comma) {
					output += ',';
				}
				needs_comma = wants_output;
				wants_output = !!column_vector[column_index];
				continue;
			}
			if(wants_output) {
				if(needs_comma) {
					needs_comma = false;
					output += ',';
				}
				output += ch;
			}
		}
		if(needs_comma) {
			output += ',';
		}
		std::cout << output;
		if(p != nullptr) {
			std::cout << p;
		}
		std::cout << std::endl;
	}
}

int main(int argc, char* argv[]) {
	char const* prog = strrchr(argv[0], '/');
	if(prog == nullptr) {
		prog = argv[0];
	} else {
		++prog;
	}

	int ch;
	while(ch = getopt(argc, argv, "c:K:h"), ch != -1) {
		switch(ch) {
		case '?':
		case 'h':
			return usage(prog);
		case 'c':
			parse_columns(optarg, true);
			break;
		case 'K':
			parse_columns(optarg, false);
			break;
		}
	}
	if(argc - optind > 1) {
		std::cerr << "too many arguments" << std::endl;
		return usage(prog);
	}
	if(all_begin == std::numeric_limits<size_t>::max() && column_vector.empty()) {
		std::cerr << "column specification not provided" << std::endl;
		exit(1);
	}
	if(argv[optind]) {
		std::ifstream fin(argv[optind]);
		if(fin) {
			csvcut(fin);
		} else {
			std::cerr << "cannot open file \"" << argv[optind] << '"' << std::endl;
			return 1;
		}
	} else {
		csvcut(std::cin);
	}

	return 0;
}
