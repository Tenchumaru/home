// g++ -std=c++11 -o $HOME/bin/csvcut -O3 csvcut.cc

#include <algorithm>
#include <fstream>
#include <iostream>
#include <istream>
#include <limits>
#include <set>
#include <string>
#include <vector>
#include <cctype>
#include <cstring>
#ifdef _WIN32
#	include <io.h>
#	define close _close
#	define open _open
#	define read _read
char const path_separator= '\\';
#else
#	include <unistd.h>
char const path_separator= '/';
#endif
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

static char const* prog;

#ifdef _WIN32
static int optind= 1;
static char* optarg;

static int getopt(int argc, char* argv[], char const* opts) {
	if(optind < argc) {
		if(argv[optind][0] == '-') {
			char const* p= std::strchr(opts, argv[optind++][1]);
			if(p == nullptr) {
				return '?';
			} else if(p[1] == ':') {
				optarg= argv[optind];
				if(optarg != nullptr) {
					++optind;
				} else {
					std::cerr << prog << ": option requires an argument -- '" <<
						*p << '\'' << std::endl;
					return '?';
				}
			}
			return *p;
		}
	}
	return -1;
}
#endif

using ivector= std::vector<size_t>;
using pvector= std::vector<char const*>;

static int usage() {
	std::cerr << "Print selected columns to standard output." << std::endl;
	std::cerr << std::endl;
	std::cerr << "usage: " << prog << " [-h] [-s] -(c|K) columns [input.csv] [...]" << std::endl << std::endl;
	std::cerr << "\t-s\tskip the header (i.e., the first line)" << std::endl;
	std::cerr << "\t-c\tcomma-separated list of 1-based column ranges to print" << std::endl;
	std::cerr << "\t-K\tcomma-separated list of 0-based column ranges to print" << std::endl << std::endl;
	std::cerr << "Options affect only those files that appear after them.  Specifying options at" << std::endl;
	std::cerr << "the end assumes standard input is the last file." << std::endl;
	return 2;
}

static pvector as_parts(std::string& line) {
	bool is_in_quote= false;
	pvector rv(1, &line[0]);
	for(auto& ch: line) {
		if(is_in_quote) {
			if(ch == '"') {
				is_in_quote= false;
			}
		} else if(ch == ',') {
			ch= '\0';
			rv.push_back(&ch + 1);
		} else if(ch == '"') {
			is_in_quote= true;
		}
	}

	return rv;
}

static size_t get_index(char const* begin, char const* end, pvector const& parts, bool is_one_based) {
	size_t index;
	if(std::all_of(begin, end, [](char ch) { return std::isdigit(ch); })) {
		// All characters are digits; parse as a number.
		index= std::atoi(begin);
		if(is_one_based) {
			if(index < 1) {
				std::cerr << prog << ": invalid column specification " << index << std::endl;
				exit(2);
			}
			--index;
		}
		if(index >= parts.size()) {
			if(is_one_based) {
				++index;
			}
			std::cerr << prog << ": invalid column specification " << index << std::endl;
			exit(2);
		}
	} else {
		// Some characters are not digits; parse as a column name.
		auto s= std::string(begin, end);
		auto it= std::find(parts.begin(), parts.end(), s);
		if(it == parts.end()) {
			std::cerr << prog << ": cannot find '" << s << "' in header" << std::endl;
			exit(1);
		}
		index= it - parts.begin();
	}
	return index;
}

static ivector output_states;
static size_t output_index;
static size_t is_writing, ignoring_commas, wrote_previous_column;

static void cut(char const* begin, char const* end) {
	if(output_index < output_states.size())
		is_writing= output_states[output_index];
	else {
		is_writing= false;
		char const* p= static_cast<char const*>(memchr(begin, '\n', end - begin));
		if(p != nullptr) {
			begin= p + 1;
			std::cout << std::endl;
			output_index= 0;
			is_writing= output_states[0];
			ignoring_commas= false;
			wrote_previous_column= false;
		} else {
			return;
		}
	}
	for(char const* p= begin; p < end; ++p) {
		if(*p == '"') {
			ignoring_commas= !ignoring_commas;
		} else if(*p == ',') {
			if(!ignoring_commas) {
				if(is_writing) {
					if(wrote_previous_column) {
						std::cout << ',';
					} else {
						wrote_previous_column= true;
					}
					std::cout.write(begin, p - begin);
				}
				begin= p + 1;
				++output_index;
				if(output_index >= output_states.size()) {
					is_writing= false;
					p= static_cast<char const*>(memchr(p, '\n', end - p));
					if(p != nullptr) {
						--p;
					} else {
						break;
					}
				} else {
					is_writing= output_states[output_index];
				}
			}
		} else if(*p == '\n') {
			if(is_writing && wrote_previous_column) {
				std::cout << ',';
			}
			begin= p + 1;
			std::cout << std::endl;
			output_index= 0;
			is_writing= output_states[0];
			ignoring_commas= false;
			wrote_previous_column= false;
		}
	}
	if(is_writing) {
		if(wrote_previous_column) {
			wrote_previous_column= false;
			std::cout << ',';
		}
		std::cout.write(begin, end - begin);
	}
}

static void parse_and_cut(char* specification, char const* file_name, bool is_one_based, bool wants_header) {
	// Check for problems.
	char const* range_token= specification != nullptr ? std::strtok(specification, ",") : nullptr;
	if(!range_token) {
		std::cerr << prog << ": no column specification provided" << std::endl << std::endl;
		exit(usage());
	}

	// Open the file or use standard input.
	std::ifstream fin(file_name);
	std::istream& sin= file_name != nullptr ? fin : std::cin;
	if(!sin) {
		std::cerr << prog << ": cannot open '" << file_name << "' for reading" << std::endl;
		exit(1);
	}

	// Read the first line since I might need it for the specification.
	std::string s;
	if(!std::getline(sin, s)) {
		return; // No data; don't bother.
	}
	pvector first_parts= as_parts(s);

	// Parse each range.
	ivector indices;
	do {
		// Check if this is a range.
		char const* end_of_range= std::strrchr(range_token, '-');
		if(end_of_range) {
			// Get the first index of the range.
			size_t first_index;
			if(range_token == end_of_range) {
				// There is no first index; it's open on the left.
				first_index= 0;
			} else {
				first_index= get_index(range_token, end_of_range, first_parts, is_one_based);
			}

			// Get the last index of the range.
			range_token= end_of_range + 1;
			size_t last_index;
			if(*range_token) {
				end_of_range= range_token + strlen(range_token);
				last_index= get_index(range_token, end_of_range, first_parts, is_one_based);
			} else {
				// There is no last index; it's open on the right.
				last_index= first_parts.size() - 1;
			}

			// Add the range to the collection of indices.
			if(last_index < first_index) {
				for(size_t i= first_index; i >= last_index; --i) {
					indices.push_back(i);
				}
			} else {
				for(size_t i= first_index; i <= last_index; ++i) {
					indices.push_back(i);
				}
			}
		} else {
			// It's not a range.
			end_of_range= range_token + strlen(range_token);
			size_t index= get_index(range_token, end_of_range, first_parts, is_one_based);
			indices.push_back(index);
		}
	} while(range_token= std::strtok(nullptr, ","), range_token);

	// Print the first line, if requested.
	if(wants_header) {
		for(size_t i= 0, n= indices.size(); i < n; ++i) {
			std::cout << first_parts[indices[i]];
			if(i < n - 1) {
				std::cout << ',';
			} else {
				std::cout << std::endl;
			}
		}
	}

	// Check if it's possible to use a faster algorithm.
	auto sorted= indices;
	std::sort(sorted.begin(), sorted.end());
	if(indices == sorted) {
		// Yes, it is; use it instead.
		int fd= file_name != nullptr ? open(file_name, O_RDONLY) : 0;
		if(fd < 0) {
			std::cerr << prog << ": cannot open '" << file_name << "' for reading" << std::endl;
			exit(1);
		} else {
			output_states.resize(indices.back() + 1);
			for(auto i: indices) {
				output_states[i]= true;
			}
			if(wants_header && fd != 0) {
				// I wrote the first line above.  Skip it here.
				char ch;
				for(int n; n= read(fd, &ch, sizeof(ch)), n > 0;) {
					if(ch == '\n')
						break;
				}
			}
			char buf[4096];
			for(int n; n= read(fd, buf, sizeof(buf)), n > 0;) {
				cut(buf, buf + n);
			}
			if(fd != 0)
				close(fd);
		}
	} else {
		// Read and print the rest of the lines.
		while(std::getline(sin, s)) {
			pvector parts= as_parts(s);
			for(size_t i= 0, n= indices.size(); i < n; ++i) {
				if(indices[i] < parts.size()) {
					std::cout << parts[indices[i]];
				}
				if(i < n - 1) {
					std::cout << ',';
				} else {
					std::cout << std::endl;
				}
			}
		}
	}
}

int main(int argc, char* argv[]) {
	std::ios_base::sync_with_stdio(false);

	// Extract the name of the program for nicer usage and error reports.
	prog= strrchr(argv[0], path_separator);
	if(prog == nullptr) {
		prog= argv[0];
	} else {
		++prog;
	}

	// Parse options and process files.
	char* specification= nullptr;
	char const* file_name= nullptr;
	bool is_one_based= false, wants_header= true;
	int ch;
	while(ch= getopt(argc, argv, "+sc:K:h"), ch != -1 || optind < argc) {
		switch(ch) {
		case '?':
		case 'h':
			return usage();
		case 's':
			wants_header= false;
			break;
		case 'c':
			specification= optarg;
			file_name= nullptr;
			is_one_based= true;
			break;
		case 'K':
			specification= optarg;
			file_name= nullptr;
			is_one_based= false;
			break;
		case -1:
			file_name= argv[optind];
			parse_and_cut(specification, file_name, is_one_based, wants_header);
			++optind;
			break;
		}
	}

	if(file_name == nullptr) {
		// Process standard input.
		parse_and_cut(specification, nullptr, is_one_based, wants_header);
	}

	return 0;
}
