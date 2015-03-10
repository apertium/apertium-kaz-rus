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
#include <string>
#include <getopt.h>
#include <ctime>
#include <clocale>

#include <apertium/utf_converter.h>
#include <apertium/string_utils.h>
#include "configure.H"
#include "AlignmentTemplate.H"
#include "TransferRule.H"
#include "zfstream.H"
#include <cmath>

using namespace std;


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

int main(int argc, char* argv[]) {
  int c;
  int option_index=0;

  double mincount=0;

  string attr_file="";

  string at_file="";
  string atx_file="";
  string criterion="count";
  bool use_zlib=false;
  bool debug=false;
  bool generalise=false;
  bool providedpatterns=false;
  bool novarsdetermined=false;
  bool nodoublecheckrestrictions=false;
  bool onepatternperrule=false;
  bool usediscardrule=false;
  bool explicitemptytags=false;
  bool emptyrestrictionsmatcheverything=false;
  bool generateChunks=false;

  cerr<<"Command line: ";
  for(int i=0; i<argc; i++)
    cerr<<argv[i]<<" ";
  cerr<<"\n\n";

  cerr<<"LOCALE: "<<setlocale(LC_ALL,"")<<"\n";


  while (true) {
    static struct option long_options[] =
      {
	{"attributes",       required_argument,  0, 'a'},
	{"atx",       required_argument,  0, 'x'},
	{"input",     required_argument,  0, 'i'},
	{"mincount",  required_argument,  0, 'm'},
	{"criterion", required_argument,  0, 'c'},
	{"explicitemptytags",            no_argument,  0, 'e'},
	{"generalise",            no_argument,  0, 'g'},
	{"providedpatterns",            no_argument,  0, 'p'},
	{"novarsdetermined",            no_argument,  0, 'n'},
	{"nodoublecheckrestrictions",            no_argument,  0, 'r'},
	{"onepatternperrule",            no_argument,  0, 'o'},
	{"usediscardrule",            no_argument,  0, 's'},
	{"emptyrestrictionsmatcheverything",            no_argument,  0, 'y'},
	{"generatechunks",            no_argument,  0, 'k'},
	{"gzip",            no_argument,  0, 'z'},
	{"debug",           no_argument,  0, 'd'},
	{"help",            no_argument,  0, 'h'},
	{"version",         no_argument,  0, 'v'},
	{0, 0, 0, 0}
      };

    c=getopt_long(argc, argv, "a:x:i:m:c:egpnroszdhvk",long_options, &option_index);
    if (c==-1)
      break;
      
    switch (c) {
	case 'a': 
      attr_file=optarg;
      break;
    case 'x': 
      atx_file=optarg;
      break;
    case 'i':
      at_file=optarg;
      break;
    case 'm':
      mincount=atof(optarg);
      break;
    case 'c':
      criterion=optarg;
      break;
    case 'z':
      use_zlib=true;
      break;
    case 'n':
     novarsdetermined=true;
	 break;
	case 'e':
	 explicitemptytags=true;
	 break;
	case 'g':
     generalise=true;
	 break;
	case 'p':
     providedpatterns=true;
	 break;
	case 'r':
	 nodoublecheckrestrictions=true;
	 break;
	case 'o':
	 onepatternperrule=true;
	 break;
	case 's':
	 usediscardrule=true;
	 break;
	case 'y':
	  emptyrestrictionsmatcheverything=true;
	  break;
    case 'd':
      debug=true;
      break;
    case 'k':
      generateChunks=true;
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

  if (at_file=="") {
    cerr<<"Error: No input file was given. You need to provide it with the --input option\n";
    help(argv[0]);
    exit(EXIT_FAILURE);
  }

  if ((criterion!="count") && (criterion!="log") && (criterion!="prod")) {
    cerr<<"Error: criterion is unknown\n";
    exit(EXIT_FAILURE);
  }

  if(attr_file.size()>0)
  {
	  istream *fattrin;
	  fattrin=new ifstream(attr_file.c_str());
	  if (fattrin->fail()) {
		cerr<<"Error: Cannot open input file '"<<attr_file<<"'\n";
		delete fattrin;
		exit(EXIT_FAILURE);
	  }
	  TransferRule::load_attributes(fattrin);
	  delete fattrin;
  }

  TransferRule::set_using_explicit_empty_tags(explicitemptytags);
  TransferRule::set_generalise(generalise);
  TransferRule::set_provided_patterns(providedpatterns);
  TransferRule::set_novarsdetermined(novarsdetermined);
  TransferRule::set_onepatternperrule(onepatternperrule);
  TransferRule::set_no_double_check_restrictions(nodoublecheckrestrictions);
  TransferRule::set_use_discard_rule(usediscardrule);
  TransferRule::set_empty_restrictions_match_everything(emptyrestrictionsmatcheverything);
  TransferRule::set_generate_chunks(generateChunks);
  
  istream *fin;
  if (use_zlib) {
    fin = new gzifstream(at_file.c_str());
  }  else {
    fin = new ifstream(at_file.c_str());
  }

  if (fin->fail()) {
    cerr<<"Error: Cannot open input file '"<<at_file<<"'\n";
    delete fin;
    exit(EXIT_FAILURE);
  }


  cerr<<"Minimum count of the alignment templates to be taken into account: "<<mincount<<"\n";
  cerr<<"Criterion to be used when interpreting alignment templates counts: "<<criterion<<"\n";

  time_t start_time, end_time;

  start_time=time(NULL);
  cerr<<"Transfer rules generation started at: "<<ctime(&start_time);

  cerr<<"Debug: "<<debug<<"\n";

  string oneat;
  wstring all_rules=L"";

  int ndiscarded=0;
  int nrules=0;
  int nats=0;

  TransferRule* tr;
  tr=new TransferRule;

  while (!fin->eof()) {
    getline(*fin,oneat);
    if(oneat.length()>0) {
	  
	  vector<wstring> *pattern=NULL;
	  
	  wstring atwstr=UtfConverter::fromUtf8(oneat);
	  if(providedpatterns)
	  {
		  int pos=atwstr.find(L'|');
		  wstring patternstr=atwstr.substr(0,pos);
		  pattern=new vector<wstring>();
		  vector<wstring> pieces= StringUtils::split_wstring(patternstr,L" ");
		  *pattern=pieces;
		  
		  atwstr=atwstr.substr(pos+1);
	  }
	  
      AlignmentTemplate at(atwstr);

      double c;
      if (criterion=="prod")
	c=((double)at.get_count())*((double)at.length());
      else if (criterion=="log")
	c=((double)at.get_count())*(1.0+log((double)at.length()));
      else //prod
	c=(double)at.get_count();

      if(c>=(double)mincount) {
	nats++;
	if (!(tr->add_alignment_template(at,pattern))) {
	  all_rules+=tr->gen_apertium_transfer_rule(debug);
	  nrules++;
	  delete tr;
	  tr=new TransferRule;
	  if (!(tr->add_alignment_template(at,pattern))) {
	    cerr<<"Error when adding an AT to an empty transfer rule\n";
	    cerr<<"This should never happen\n";
	    exit(EXIT_FAILURE);
	  }
	}
      } else {
	ndiscarded++;
      }
      
      delete pattern;
    }
  }
  
  if (tr->get_number_alignment_templates()>0) {
    all_rules+=tr->gen_apertium_transfer_rule(debug);
    nrules++;
  }
  

  delete tr;
  delete fin;

  cout<<UtfConverter::toUtf8(TransferRule::gen_apertium_transfer_head(debug));
  cout<<UtfConverter::toUtf8(all_rules);
  cout<<UtfConverter::toUtf8(TransferRule::gen_apertium_transfer_foot(debug));

  cerr<<ndiscarded<<" alignment templates were discarded because their counts were below the minimum allowed\n";
  cerr<<nrules<<" transfer rules were generated\n";
  cerr<<nats<<" alignment templates were taken into account\n";

  end_time=time(NULL);
  cerr<<"Transfer rules generation finished at: "<<ctime(&end_time)<<"\n";
  cerr<<"Transfer rules generation took "<<difftime(end_time, start_time)<<" seconds\n";
}
