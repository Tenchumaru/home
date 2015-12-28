#include <stdio.h>
#include <stdbool.h>
#include <string.h>

#define arg_is_dash(n) (argv[n][0] == '-' && !argv[n][1])

static int usage(char const* prog)
{
	fprintf(stderr, "usage: %s [-h] [-b] [-p] [-r ch] [-u] [-z] [input_file [output_file]]\n", prog);
	fputs("use -b to remove BOM from input\n", stderr);
	fputs("use -p to ensure all characters are printable\n", stderr);
	fputs("use -r to specify a replacement character\n", stderr);
	fputs("use -u to strip CRs from input\n", stderr);
	fputs("use -z to strip DOS EOF marker from input\n", stderr);
	return 2;
}

static int replacement_ch= EOF;
static bool strip_dos_eof= false, strip_cr= false, wants_printable= false;

static void print(int ch, FILE* fout)
{
	if((!strip_dos_eof || ch != 26) && (!strip_cr || ch != '\r'))
	{
		if(replacement_ch == EOF)
			ch &= 0x7f;
		else if(ch & ~0x7f)
			ch= replacement_ch;
		if(wants_printable)
		{
			if(ch < ' ' && (!ch || !strchr("\t\n\v\r", ch)))
				ch= replacement_ch != EOF ? replacement_ch : ' ';
			else if('~' < ch)
				ch= replacement_ch != EOF ? replacement_ch : '~';
		}
		putc(ch, fout);
	}
}

int main(int argc, char* argv[])
{
	char const* prog= argv[0];
	bool remove_bom= false;
	while(argc > 1 && argv[1][0] == '-' && argv[1][1])
	{
		switch(argv[1][1])
		{
		case 'h':
			return usage(prog);
		case 'b':
			remove_bom= true;
			break;
		case 'p':
			wants_printable= true;
			break;
		case 'r':
			if(argc < 3)
				return usage(prog);
			replacement_ch= argv[2][0];
			--argc, ++argv;
			break;
		case 'u':
			strip_cr= true;
			break;
		case 'z':
			strip_dos_eof= true;
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
		else
			print(ch, fout);
	}
	while(ch= getc(fin), ch != EOF)
		print(ch, fout);
	if(argc > 1)
	{
		fclose(fin);
		if(argc > 2)
			fclose(fout);
	}
	return 0;
}
