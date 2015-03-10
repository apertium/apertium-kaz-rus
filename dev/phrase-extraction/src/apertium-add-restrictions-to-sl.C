/*
 * Copyright (C) 2006-2007 Felipe Sánchez-Martínez
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
 * 02111-1307, USA.
 */

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <getopt.h>
#include <ctime>
#include <clocale>

#include <lttoolbox/fst_processor.h>
#include <apertium/utf_converter.h>

#include "Utils.H"
#include <cmath>



using namespace std;

void replaceAll(std::wstring& str, const std::wstring& from, const std::wstring& to) {
    if(from.empty())
        return;
    size_t start_pos = 0;
    while((start_pos = str.find(from, start_pos)) != std::wstring::npos) {
        str.replace(start_pos, from.length(), to);
        start_pos += to.length(); // In case 'to' contains 'from', like replacing 'x' with 'yx'
    }
}

void help(char *name) {
  cerr<<"USAGE:\n";
  cerr<<name<<" --input alignment_templates [--mincount <n>] [--criterion count|log|prod] [--gzip] [--debug]\n\n";
  cerr<<"ARGUMENTS: \n"
      <<"   --input|-i: Specify a file containing the alignment templates (AT) to work with\n"
      <<"   --mincount|-m: Specify the minimum count of the alignment templates to be taken into account\n"
      <<"   --criterion|-c: Specify which criterion must be used when considering the count of each AT\n"
      <<"       Possible values: \n"
      <<"         count: Use directly the count provided with the AT (default)\n"
      <<"         log: The count is multiplied by 1 plus the log of the number of SL words of the AT\n"
      <<"         prod: The count is multiplied by the number of SL words of the AT\n"
      <<"   --gzip|-z: Tell the program that the input file is gziped\n"
      <<"   --debug|-d: Print debug information in each generated rule\n"
      <<"   --help|-h: Show this help\n"
      <<"   --version|-v: Show version information\n\n";
  cerr<<"IMPORTANT NOTES: \n"
      <<"   * The input file MUST contain the alignment templates (AT) ordered by its source-language\n"
      <<"     part, i. e., those AT with the same source-language part MUST be together\n"
      <<"   * It is SUPOSSED that in the input file each AT is UNIQ\n"
      <<"   * Write to the standard output a file containing transfer rules in the apertium XML format\n";      
}

/**
 *	Reads from stdin until it finds an instace of "character" not preceeded by '\'
 * 
 */
std::wstring readRemainingWord(const wchar_t readedBefore, const wchar_t character)
{
	wchar_t c;
	std::wstring output;
	output+=readedBefore;
	wchar_t readedB = readedBefore;
	
	c = getwchar_unlocked();
	
	while( !(c==character && readedB!=L'\\') )
	{
		output+=c;
		if(readedB==L'\\')
			readedB=L'\0';
		else
			readedB=c;
		c = getwchar_unlocked();
	}
	
	
	
	return output;
}

int processWord(std::wstring &lex)
{
	int count;

	std::wstring readed = readRemainingWord(L'^',L'$');
	readed.erase(0,1);
	lex = readed;
	
	return count;
}

int main(int argc, char* argv[]) {
  int op;
  int option_index=0;

  double mincount=0;

  string bil_file="";
  bool use_zlib=false;
  bool debug=false;

  cerr<<"Command line: ";
  for(int i=0; i<argc; i++)
    cerr<<argv[i]<<" ";
  cerr<<"\n\n";

  cerr<<"LOCALE: "<<setlocale(LC_ALL,"")<<"\n";


  while (true) {
    static struct option long_options[] =
      {
	{"biling",       required_argument,  0, 'b'},
	{"help",            no_argument,  0, 'h'},
	{"version",         no_argument,  0, 'v'},
	{0, 0, 0, 0}
      };

    op=getopt_long(argc, argv, "b:hv",long_options, &option_index);
    if (op==-1)
      break;
      
    switch (op) {
    case 'b': 
      bil_file=optarg;
      break;
    case 'h': 
      help(argv[0]);
      exit(EXIT_SUCCESS);
      break;
    case 'v':
      cerr<<"LICENSE:\n\n"
	  <<"   Copyright (C) 2006-2007 Felipe Sánchez-Martínez\n\n"
	  <<"   This program is free software; you can redistribute it and/or\n"
	  <<"   modify it under the terms of the GNU General Public License as\n"
	  <<"   published by the Free Software Foundation; either version 2 of the\n"
	  <<"   License, or (at your option) any later version.\n"
	  <<"   This program is distributed in the hope that it will be useful, but\n"
	  <<"   WITHOUT ANY WARRANTY; without even the implied warranty of\n"
	  <<"   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU\n"
	  <<"   General Public License for more details.\n"
	  <<"\n"
	  <<"   You should have received a copy of the GNU General Public License\n"
	  <<"   along with this program; if not, write to the Free Software\n"
	  <<"   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA\n"
	  <<"   02111-1307, USA.\n";
      exit(EXIT_SUCCESS);
      break;    
    default:
      help(argv[0]);
      exit(EXIT_FAILURE);
      break;
    }
   }
  

  if (bil_file=="") {
    cerr<<"Error: No bilingual dictionary file was given. You need to provide it with the --biling option\n";
    help(argv[0]);
    exit(EXIT_FAILURE);
  }
  
  FILE *fbil_dic=NULL;
  fbil_dic=fopen(bil_file.c_str(), "r");
  if (!fbil_dic) {
    cerr<<"Error: Cannot open bilingual dictionary file '"<<bil_file<<"\n";
    exit(EXIT_FAILURE);
  }
  FSTProcessor fstp;
  fstp.load(fbil_dic);
  fstp.initBiltrans();
  fclose(fbil_dic);
  
 
  
  wstring translation,lex;


  wchar_t c;
  c= getwchar_unlocked();
	
  while(c!=EOF)
  {
	  if(c ==L'^')
	  {
		  processWord(lex);
		  if(lex.size() > 0 && lex[0]!=L'*')
		  {
			  translation=fstp.biltransWithoutQueue(lex, false);
			  int posStartTagsSL=lex.find(L'<');
			  int posStartTagsTL=translation.find(L'<');
			  
			  wstring slTags=lex.substr(posStartTagsSL);
			  wstring slLemma=lex.substr(0,posStartTagsSL);
			  wstring tlLemma=translation.substr(0,posStartTagsTL);
			  wstring tlTags=translation.substr(posStartTagsTL);
			  
			  std::wcout<<L'^'<<slLemma;
			  replaceAll(tlTags,L"<",L"<RES");
			  std::wcout<<tlTags;
			  std::wcout<<slTags<<L'$';
		  }
		  else
		  {
			  std::wcout<<L'^'<<lex<<L'$';
		  }
	  }
	  else
	  {
		  std::wcout<<c;
		  if(c==L'\0')
		  {
		  	  std::wcout<<L'\n';
			  std::wcout.flush();
		  }
	  }
	c= getwchar_unlocked();
  }
  
//  delete fin;

}

