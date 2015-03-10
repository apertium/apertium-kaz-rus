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


void help(char *name) {
  cerr<<"USAGE:\n";
  cerr<<name<<" --biling <compiled_bilingual_dictionary> [--withqueue] \n\n";
  cerr<<"ARGUMENTS: \n"
      <<"   --biling|-b: Specify the compiled bilingual dictionary\n"
      <<"   --withqueue|-1: Tell the program to include all the tags in TL lexical forms. If not, only tags present in the bilingual dictionary are included.\n";
}

int main(int argc, char* argv[]) {
  int c;
  int option_index=0;

  double mincount=0;

  string bil_file="";
  bool use_zlib=false;
  bool debug=false;
  bool withqueue=false;
  bool explicitempty=false;

  cerr<<"Command line: ";
  for(int i=0; i<argc; i++)
    cerr<<argv[i]<<" ";
  cerr<<"\n\n";

  cerr<<"LOCALE: "<<setlocale(LC_ALL,"")<<"\n";


  while (true) {
    static struct option long_options[] =
      {
	{"biling",       required_argument,  0, 'b'},
	{"withqueue",       no_argument,  0, 'q'},
	{"help",            no_argument,  0, 'h'},
	{"explicitempty",            no_argument,  0, 'e'},
	{"version",         no_argument,  0, 'v'},
	{0, 0, 0, 0}
      };

    c=getopt_long(argc, argv, "b:qhve",long_options, &option_index);
    if (c==-1)
      break;
      
    switch (c) {
    case 'b': 
      bil_file=optarg;
      break;
    case 'q':
	  withqueue=true;
	  break;
	case 'e':
	  explicitempty=true;
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
  
  istream *fin = &cin;
  
  if (fin->fail()) {
    cerr<<"Error: Cannot open input file '"<<bil_file<<"'\n";
    delete fin;
    exit(EXIT_FAILURE);
  }

  string line;
  vector<string> words;
  wstring translation;
  wstring wline;
  string delimiter="\t";

  while (!fin->eof()) {
    getline(*fin,line);
    if(line.length()>0) {
		stringstream ss;
		words=Utils::split_string(line,delimiter);
		for (vector<string>::iterator it = words.begin(); it!=words.end(); ++it){
			if(withqueue)
				translation=fstp.biltrans(UtfConverter::fromUtf8(*it), false);
			else
				translation=fstp.biltransWithoutQueue(UtfConverter::fromUtf8(*it), false);
			if (it!=words.begin()){
				ss << "\t";
			}
			if (explicitempty &&  translation.size() == 0 )
				ss << "__EMPTY_WORD__";
			else
				ss << UtfConverter::toUtf8(translation);
		}
		cout<<ss.str()<<endl;
   }
  }
  
//  delete fin;

}

