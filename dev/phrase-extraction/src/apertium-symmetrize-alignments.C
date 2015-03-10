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

#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <string>
#include <getopt.h>
#include <ctime>
#include <clocale>
#include <apertium/utf_converter.h>

#include "configure.H"
#include "Alignment.H"
#include "zfstream.H"

using namespace std;


void help(char *name) {
  cerr<<"USAGE:\n";
  cerr<<name<<" --input1 alignments1 --input2 alignments2 --output alignments --operation union|intersection|refined [--gzip]\n\n";
  cerr<<"ARGUMENTS: \n"
      <<"   --input1|-i: Specify a file containing alignments\n"
      <<"   --input2|-j: Specify a file containing alignments\n"
      <<"   --output|-o: Specify the file in which the intesection between both alignments must be writen\n"
      <<"   --operation|-p: Specify the operation to be performed: \n"
      <<"         union: perform the union of both aligments\n"
      <<"         intersection: perform the intersection of both alignments\n"
      <<"         refined: perform the refined intersection of both alignments\n"
      <<"   --gzip|-z: Tell the program that the input files are gziped, the output will be gziped too\n"
      <<"   --help|-h: Show this help\n"
      <<"   --version|-v: Show version information\n";
}

int main(int argc, char* argv[]) {
  int c;
  int option_index=0;

  string al1_file="";
  string al2_file="";
  string alout_file="";

  string operation="";

  bool use_zlib=false;

  cerr<<"Command line: ";
  for(int i=0; i<argc; i++)
    cerr<<argv[i]<<" ";
  cerr<<"\n\n";

  cerr<<"LOCALE: "<<setlocale(LC_ALL,"")<<"\n";


  while (true) {
    static struct option long_options[] =
      {
	{"input1",    required_argument,  0, 'i'},
	{"input2",    required_argument,  0, 'j'},
	{"output",    required_argument,  0, 'o'},
	{"operation", required_argument,  0, 'p'},
	{"gzip",          no_argument,  0, 'z'},
	{"help",          no_argument,  0, 'h'},
	{"version",       no_argument,  0, 'v'},
	{0, 0, 0, 0}
      };

    c=getopt_long(argc, argv, "i:j:o:p:zhv",long_options, &option_index);
    if (c==-1)
      break;
      
    switch (c) {
    case 'i':
      al1_file=optarg;
      break;
    case 'j':
      al2_file=optarg;
      break;
    case 'o':
      alout_file=optarg;
      break;
    case 'p':
      operation=optarg;
      break;
    case 'z':
      use_zlib=true;
      break;
    case 'h': 
      help(argv[0]);
      exit(EXIT_SUCCESS);
      break;
    case 'v':
      cerr<<PACKAGE_STRING<<"\n";
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

  if (al1_file=="") {
    cerr<<"Error: No input1 file was given. You need to provide it with the --input1 option\n";
    help(argv[0]);
    exit(EXIT_FAILURE);
  }

  if (al2_file=="") {
    cerr<<"Error: No input2 file was given. You need to provide it with the --input2 option\n";
    help(argv[0]);
    exit(EXIT_FAILURE);
  }

  if (alout_file=="") {
    cerr<<"Error: No output file was given. You need to provide it with the --output option\n";
    help(argv[0]);
    exit(EXIT_FAILURE);
  }
  
  if (operation=="") {
    cerr<<"Error: No operation to be performed was given. You need to provide it with the --operation option\n";
    help(argv[0]);
    exit(EXIT_FAILURE);
  }

  if ((operation!="union")&&(operation!="intersection")&&(operation!="refined")) {
    cerr<<"Error: The operation to perform is unknown. It should be 'union', 'intersection', or 'refined'\n";
    help(argv[0]);
    exit(EXIT_FAILURE);
  }

  if (operation=="refined")
    operation="refined intersection";

  cerr<<"Aligments to operate with come from files '"<<al1_file<<"' and '"<<al2_file<<"'\n";


  istream *fal1;
  if (use_zlib) {
    fal1 = new gzifstream(al1_file.c_str());
  }  else {
    fal1 = new ifstream(al1_file.c_str());
  }

  if (fal1->fail()) {
    cerr<<"Error: Cannot open input file '"<<al1_file<<"'\n";
    delete fal1;
    exit(EXIT_FAILURE);
  }

  istream *fal2;
  if (use_zlib) {
    fal2 = new gzifstream(al2_file.c_str());
  }  else {
    fal2 = new ifstream(al2_file.c_str());
  }

  if (fal2->fail()) {
    cerr<<"Error: Cannot open input file '"<<al2_file<<"'\n";
    delete fal1;
    delete fal2;
    exit(EXIT_FAILURE);
  }

  ostream *fout;
  if(use_zlib) {
    fout = new gzofstream(alout_file.c_str());
  } else {
    fout = new ofstream(alout_file.c_str());
  }

  if (fout->fail()) {
    cerr<<"Error: Cannot open output file '"<<alout_file<<"'\n";
    delete fal1;
    delete fal2;
    delete fout;
    exit(EXIT_FAILURE);
  }

  time_t start_time, end_time;

  start_time=time(NULL);
  cerr<<"Alignment "<<operation<<" started at: "<<ctime(&start_time);

  string al1;
  string al2;

  long nal=0;

  while ((!fal1->eof())&&(!fal2->eof())) {
    getline(*fal1,al1);
    getline(*fal2,al2);

    if ((al1.length()>0) && (al2.length()>0)) {
      nal++;
      Alignment alig1(UtfConverter::fromUtf8(al1));
      Alignment alig2(UtfConverter::fromUtf8(al2));

      bool opok;
      if (operation=="union")
	opok=alig1.unionn(alig2);
      else if (operation=="intersection")
	opok=alig1.intersection(alig2);
      else 
	opok=alig1.refined_intersection(alig2);

      if (opok)
	(*fout)<<alig1<<"\n";	
      else 
	cerr<<"Warning: the alignment at line "<<nal<<" will be discarded\n";

      if ((nal%10000)==0)
	cerr<<nal<<" alignments processed\n";
    }

    if ((fal1->eof()!=fal2->eof()) || (fal1->good()!=fal2->good())) {
      cerr<<"Error: The two input file do not contain the same number of alignments.\n";
      exit(EXIT_FAILURE);
    }
				    
  }

  end_time=time(NULL);
  cerr<<"Alignment "<<operation<<" finished at: "<<ctime(&end_time)<<"\n";
  cerr<<"Alignment "<<operation<<" took "<<difftime(end_time, start_time)<<" seconds\n";

  delete fal1;
  delete fal2;
  delete fout;
}
