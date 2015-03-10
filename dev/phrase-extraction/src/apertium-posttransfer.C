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
#include <clocale>
#include <vector>
#include <deque>
#include <algorithm>
#include <wchar.h>

#include "configure.H"
#include "PTXReader.H"
#include "Utils.H"

using namespace std;

class LUComparer {
public:
  bool operator()(const vector<wstring>& e1, const vector<wstring>& e2)  const {
    //True if e1>e2
    return (e1.size() > e2.size());
  }
};

//True if there are more words to read
bool next_word (wstring& ignored_string, wstring& word) {
  wchar_t c, prev_c=L' ';
  bool finish=false;
  bool reading_word=false;

  ignored_string=L"";
  word=L"";

  while (!finish) {
    wcin>>c;

    if (wcin.fail()) {
      if (reading_word) {
        wcerr<<L"Error in apertium-posttransfer::next_word while reading input word\n";
        wcerr<<L"Malformed input string, at '"<<c<<"'\n";
        exit(EXIT_FAILURE);
      } else {
	return false;
      }
    }

    if ((c==L'^') && (prev_c!=L'\\') && (!reading_word)) {
      reading_word=true;
    } else if ((c==L'$') && (prev_c!=L'\\') && (reading_word)) {
      finish=true;
    } else {
      if (reading_word)
        word+=c;
      else
        ignored_string+=c;
    }
    prev_c=c;
  }

  if ((word.length()==0) && (ignored_string.length()==0))
    return false;

  return true;
}

//True if there was a merged multilexical unit
bool merge_and_print_mlu(vector<vector<wstring> >& mlu, deque<pair<wstring, wstring> >& buffer) {

  for(unsigned i=0; i<mlu.size(); i++) {
    if (mlu[i].size() <= buffer.size()) {

      bool is_mlu=true;
      for(unsigned j=0; (j<mlu[i].size()) && (is_mlu); j++) {
	wstring tags=Utils::get_tags(buffer[j].second);
	if (tags.find(mlu[i][j])!=0)
	  is_mlu=false;
      }
      if (is_mlu) {
	for(unsigned j=0; j<mlu[i].size(); j++) {
	  //Only if format information is present
	  if ((j==0) || (buffer[j].first.find(L"[")!=wstring::npos))
	    wcout<<buffer[j].first;
	}

	wcout<<L"^";
	for(unsigned j=0; j<mlu[i].size(); j++) {
	  if(j>0)
	    wcout<<L"+";
	  wcout<<buffer[0].second;
	  buffer.pop_front();
	}
	wcout<<L"$";
	return true;
      }
    }
  }

  return false;
}

void help(char *name) {
  cerr<<"USAGE:\n";
  cerr<<name<<" --ptx file.ptx\n\n";

  cerr<<"ARGUMENTS: \n"
      <<"   --ptx|-x: Specify the configuration file to use when performing post-transfer operations\n";

  cerr<<"NOTE: \n"
      <<"   This program is meant to undo operations made by apertium-pretransfer that has not \n"
      <<"   been reverted by the apertium-transfer itself.\n";
}

int main(int argc, char* argv[]) {
  int c;
  int option_index=0;

  string ptx_file="";

  //cerr<<"Command line: ";
  //for(int i=0; i<argc; i++)
  //  cerr<<argv[i]<<" ";
  //cerr<<"\n\n";

  cerr<<"LOCALE: "<<setlocale(LC_ALL,"")<<"\n";


  while (true) {
    static struct option long_options[] =
      {
	{"ptx",       required_argument,  0, 'x'},
	{"help",            no_argument,  0, 'h'},
	{"version",         no_argument,  0, 'v'},
	{0, 0, 0, 0}
      };

    c=getopt_long(argc, argv, "x:hv",long_options, &option_index);
    if (c==-1)
      break;
      
    switch (c) {
    case 'x': 
      ptx_file=optarg;
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

  if (ptx_file=="") {
    cerr<<"Error: No configuration file was given. You need to provide it with the --ptx option\n";
    help(argv[0]);
    exit(EXIT_FAILURE);
  }

  PTXReader reader;

  reader.read(ptx_file);

  vector<vector<wstring> > mlu;
  mlu=reader.get_all_mlu();

  //Whe reading from the input stream '*all* characters must be
  //processed, including ' ','\n', .....
  wcin.unsetf(ios::skipws);

  //Sort lu for each mlu so that the longest one appears first
  LUComparer comparer;
  sort(mlu.begin(), mlu.end(), comparer);

  //Determine which is the longest mlu
  //unsigned buffer_max_size=0;  
  //for(unsigned i=0; i<mlu.size(); i++) {
  //  if (mlu[i].size()>buffer_max_size)
  //    buffer_max_size=mlu[i].size();
  //}
  
  unsigned buffer_max_size=0;
  if (mlu.size()>0)
    buffer_max_size=mlu[0].size();

  //cerr<<"SIZE: "<<buffer_max_size<<"\n";

  deque<pair<wstring, wstring> > buffer;
  pair<wstring, wstring> all;

  wstring word, ignored_string;
  while(next_word(ignored_string, word)) {

    //cerr<<"w: "<<ignored_string<<"_"<<word<<"\n";

    all.first=ignored_string;
    all.second=word;
    buffer.push_back(all);

    if(buffer.size()>buffer_max_size) {
      wcout<<buffer[0].first<<L"^"<<buffer[0].second<<L"$";
      buffer.pop_front();
    }

    if(buffer.size()==buffer_max_size) {
      //Test if there is a multilexical unit in the buffer,
      //in such a case, merge and print it out
      merge_and_print_mlu(mlu, buffer);
    }
  }

  //Empty the buffer
  while(buffer.size()>0) {
    if (!merge_and_print_mlu(mlu, buffer)) {
      wcout<<buffer[0].first<<L"^"<<buffer[0].second<<L"$";
      buffer.pop_front();
    }
  }

  wcout<<ignored_string;
}
