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

#include "PTXReader.H"
#include <lttoolbox/xml_parse_util.h>
#include <apertium/string_utils.h>

void
PTXReader::copy(PTXReader const &o) {
  cerr<<"Warning in PTXReader::copy: Not implemented\n";
}

void
PTXReader::destroy() {
}

PTXReader::PTXReader() {
}

PTXReader::~PTXReader() {
  destroy();
}

PTXReader::PTXReader(PTXReader const &o) {
  copy(o);
}


void
PTXReader::step() {
  int retval = xmlTextReaderRead(reader);
  if(retval != 1)
  {
    parseError(L"unexpected EOF");
  }
  name = XMLParseUtil::towstring(xmlTextReaderConstName(reader));
  type = xmlTextReaderNodeType(reader);

  //cerr<<"In PTXReader::step: name='"<<name<<"', type="<<type<<"\n";
}

PTXReader &
PTXReader::operator =(PTXReader const &o) {
  if(this != &o)
  {
    destroy();
    copy(o);
  }
  return *this;
}

wstring
PTXReader::attrib(wstring const &name) {
  return XMLParseUtil::attrib(reader, name);
} 

void
PTXReader::parseError(wstring const &message) {
  cerr << "Error: (" << xmlTextReaderGetParserLineNumber(reader);
  wcerr << L"): " << message << L"." << endl;
  exit(EXIT_FAILURE);
}


void 
PTXReader::proc_mlu() {
  vector<wstring> one_mlu;
  if(name == L"mlu") {
    step();
    while (!((name==L"mlu") && (type==XML_READER_TYPE_END_ELEMENT))) {
      if (name==L"lu")
	proc_lu(one_mlu);
      step();
    }
  }

  mlu.push_back(one_mlu);

  while(name == L"#text" || name == L"#comment") 
    step();
}

void
PTXReader::proc_lu(vector<wstring>& one_mlu) {
  wstring tags=attrib(L"tags");
  if (tags.length()==0)
    parseError(L"mandatory attribute 'tags' cannot be empty");
  else if (tags[0]=='*')
    parseError(L"mandatory attribute 'tags' cannot start with '*'");
  
  wstring::size_type p=tags.find(L"*",0);
  if ((p!=wstring::npos) && (p!=(tags.size()-1)))
     parseError(L"mandatory attribute 'tags' cannot cannot have a '*' in the middle");

  tags=StringUtils::substitute(tags, L".*",L"");
  tags=StringUtils::substitute(tags, L".", L"><");
  tags=L"<"+tags+L">";

  one_mlu.push_back(tags);
}

void
PTXReader::read(string const &filename) {
  reader = xmlReaderForFile(filename.c_str(), NULL, 0);
  if(reader == NULL) {
    cerr << "Error: Cannot open '" << filename << "'." << endl;
    exit(EXIT_FAILURE);
  }

  step();

  while(name == L"#text" || name == L"#comment") 
    step();
  
  if(name == L"posttransfer") {
    step();
    while (!((name==L"posttransfer") && (type==XML_READER_TYPE_END_ELEMENT))) {
      if (name==L"mlu")
	proc_mlu();
      step();
    }
  }

  xmlFreeTextReader(reader);
  xmlCleanupParser();
}


vector<vector<wstring> > 
PTXReader::get_all_mlu() {
  return mlu;
}
