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


#include "ATXReader.H"
#include <lttoolbox/xml_parse_util.h>

void
ATXReader::copy(ATXReader const &o) {
  cerr<<"Warning in ATXReader::copy: Not implemented\n";
}

void
ATXReader::destroy() {
}

ATXReader::ATXReader() {
}

ATXReader::~ATXReader() {
  destroy();
}

ATXReader::ATXReader(ATXReader const &o) {
  copy(o);
}


void
ATXReader::step() {
  int retval = xmlTextReaderRead(reader);
  if(retval != 1)
  {
    parseError(L"unexpected EOF");
  }
  name = XMLParseUtil::towstring(xmlTextReaderConstName(reader));
  type = xmlTextReaderNodeType(reader);

  //cerr<<"In ATXReader::step: name='"<<name<<"', type="<<type<<"\n";
}

ATXReader &
ATXReader::operator =(ATXReader const &o) {
  if(this != &o)
  {
    destroy();
    copy(o);
  }
  return *this;
}

wstring
ATXReader::attrib(wstring const &name) {
  return XMLParseUtil::attrib(reader, name);
} 

void
ATXReader::parseError(wstring const &message) {
  wcerr << L"Error: (" << xmlTextReaderGetParserLineNumber(reader);
  wcerr << L"): " << message << L"." << endl;
  exit(EXIT_FAILURE);
}

void
ATXReader::procLexicalizedWord(LexicalizedWords& cw) {
  wstring tags=attrib(L"tags");
  if (tags.length()==0)
    parseError(L"mandatory attribute 'tags' cannot be empty");
  else if (tags[0]=='*')
    parseError(L"mandatory attribute 'tags' cannot start with '*'");

  //cerr<<attrib("lemma")<<" "<<attrib("tags")<<"\n";
  cw.insert(attrib(L"lemma"), attrib(L"tags"));
}

void 
ATXReader::procSource() {
  if(name == L"lexicalized-words") {
    step();
    while (!((name==L"lexicalized-words") && (type==XML_READER_TYPE_END_ELEMENT))) {
      if (name==L"lexicalized-word")
	procLexicalizedWord(source_lexicalized_words);
      step();
    }
  }

  while(name == L"#text" || name == L"#comment") 
    step();
  
  while (!((name==L"source") && (type==XML_READER_TYPE_END_ELEMENT))) 
    step();
  
  step();

  while(name == L"#text" || name == L"#comment") 
    step();
}

void 
ATXReader::procTarget() {
  if(name == L"lexicalized-words") {
    step();
    while (!((name==L"lexicalized-words") && (type==XML_READER_TYPE_END_ELEMENT))) {
      if (name==L"lexicalized-word")
	procLexicalizedWord(target_lexicalized_words);
      step();
    }
  }

  while(name == L"#text" || name == L"#comment") 
    step();  

  while (!((name==L"target") && (type==XML_READER_TYPE_END_ELEMENT))) 
    step();
  
  step();

  while(name == L"#text" || name == L"#comment")
    step();  
}

void
ATXReader::read(string const &filename) {
  reader = xmlReaderForFile(filename.c_str(), NULL, 0);
  if(reader == NULL) {
    cerr << "Error: Cannot open '" << filename << "'." << endl;
    exit(EXIT_FAILURE);
  }

  step();

  while(name == L"#text" || name == L"#comment") 
    step();
  
  if(name == L"transfer-at") {
    source_lang=attrib(L"source");
    target_lang=attrib(L"target");
    step();
    while(name == L"#text" || name == L"#comment") 
      step();
  }

  if (name == L"source") {
    step();
    while(name == L"#text" || name == L"#comment") 
      step();
    
    procSource();
  }

  if (name == L"target") {
    step();
    while(name == L"#text" || name == L"#comment") 
      step();
    
    procTarget();
  }

  xmlFreeTextReader(reader);
  xmlCleanupParser();

  //cerr<<"source="<<source_lang<<"\n";
  //cerr<<"target="<<target_lang<<"\n";
}

LexicalizedWords&
ATXReader::get_source_lexicalized_words() {
  return source_lexicalized_words;
}

LexicalizedWords&
ATXReader::get_target_lexicalized_words() {
  return target_lexicalized_words;
}

wstring 
ATXReader::get_source_language() {
  return source_lang;
}

wstring 
ATXReader::get_target_language() {
  return target_lang;
}
