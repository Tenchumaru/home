#include <stdio.h>
#include <stdbool.h>

#define arg_is_dash(n) (argv[n][0] == '-' && !argv[n][1])

static int usage(char const* prog)
{
	fprintf(stderr, "usage: %s [-h] [-b] [-u] [input_file [output_file]]\n", prog);
	fputs("use -b to remove BOM from input\n", stderr);
	fputs("use -u to strip CRs from input\n", stderr);
	return 2;
}

int main(int argc, char* argv[])
{
	char const* prog= argv[0];
	bool remove_bom= false, strip_cr= false;
	while(argc > 1 && argv[1][0] == '-' && argv[1][1])
	{
		switch(argv[1][1])
		{
		case 'h':
			return usage(prog);
		case 'b':
			remove_bom= true;
			break;
		case 'u':
			strip_cr= true;
			break;
		default:
			return usage(prog);
		}
		--argc, ++argv;
	}
	if(argc > 3)
		return usage(prog);
	FILE* fin= stdin;
	FILE* fout= stdout;
	if(argc > 1 && !arg_is_dash(1))
	{
		fin= fopen(argv[1], "r");
		if(!fin)
		{
			fprintf(stderr, "%s: cannot open %s for reading\n", prog, argv[1]);
			return 1;
		}
	}
	if(argc > 2 && !arg_is_dash(2))
	{
		fout= fopen(argv[2], "w");
		if(!fout)
		{
			fprintf(stderr, "%s: cannot open %s for writing\n", prog, argv[2]);
			return 1;
		}
	}
	int ch;
	if(remove_bom)
	{
		ch= getc(fin);
		if(ch == 0xef)
		{
			getc(fin);
			getc(fin);
		}
		else if(!strip_cr || ch != '\r')
			putc(ch & 0x7f, fout);
	}
	while(ch= getc(fin), ch != EOF)
	{
		if(!strip_cr || ch != '\r')
			putc(ch & 0x7f, fout);
	}
	if(argc > 1)
	{
		fclose(fin);
		if(argc > 2)
			fclose(fout);
	}
	return 0;
}
