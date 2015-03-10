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


#include "LexicalizedWords.H"
#include <string>
#include <wchar.h>
#include <apertium/utf_converter.h>

LexicalizedWords::LexicalizedWords() {
  global_regexp=L"";
  regexp_was_compiled=false;
}

LexicalizedWords::LexicalizedWords(const LexicalizedWords& cw) {
  copy(cw);
}
    
LexicalizedWords::~LexicalizedWords() {
  destroy();
}

void 
LexicalizedWords::insert(wstring lemma, wstring tags) {
  //When calling this method, it is supossed that tags is not empty
  //and it does not start with '*'

  if (regexp_was_compiled) {
    cerr<<"Error in LexicalizedWords::insert: No more close words can be added after calling LexicalizedWords::insert_ends\n";
    exit(EXIT_FAILURE);
  }

  pair<wstring, wstring> cw;
  unsigned pos;

  cw.first=lemma;
  cw.second=tags;

  lexicalized_words.insert(cw);

  wstring regular_exp=tags;

  //cerr<<"REG EXP(0): "<<regular_exp<<"\n";

  regular_exp=L"<"+regular_exp;

  //cerr<<"REG EXP(1): "<<regular_exp<<"\n";

  //Some dots must be replaced by the corresponding string "><" or ">"
  pos=0;
  while ((pos=regular_exp.find(L".", pos)) != static_cast<unsigned int>(wstring::npos)) {
    if (regular_exp[pos+1]!='*') {
      regular_exp.replace(pos, 1, L"><");
      pos+=2;
    } else {
      regular_exp.replace(pos, 1, L">");
      pos++;
    }
  }

  //cerr<<"REG EXP(2): "<<regular_exp<<"\n";

  if (regular_exp[regular_exp.size()-1]!='*')
    regular_exp=regular_exp+L">";

  //cerr<<"REG EXP(3): "<<regular_exp<<"\n";

  //All starts must be replaced by the corresponding regular
  //expression
  pos=0;
  while ((pos=regular_exp.find(L"*", pos)) != static_cast<unsigned int>(wstring::npos)) {
    regular_exp.replace(pos, 1, TAGS);
    pos+=wcslen(TAGS);
  }

  //cerr<<"REG EXP(4): "<<regular_exp<<"\n";

  if (lemma.length()>0)
    regular_exp=L"(^"+lemma+L")"+L"("+regular_exp+L")$";
  else
    regular_exp =L"[^<]" + regular_exp + L"$";

  regular_exp=L"("+ regular_exp +L")";

  //cerr<<"LexicalizedWords::insert: lemma='"<<lemma<<"', tags='"<<tags<<"', regexp='"<<regular_exp<<"'\n";

  if (global_regexp.length()>0)
    global_regexp+= L"|";
  global_regexp+=regular_exp;

  //cerr<<"Global reg exp: "<<global_regexp<<"\n\n";
}

void 
LexicalizedWords::insert_ends() {
  //Compile the global_regexp
  int res=regcomp(&compiled_global_regexp, 
		  UtfConverter::toUtf8(global_regexp).c_str(), 
		  REG_EXTENDED | REG_ICASE | REG_NOSUB | REG_UTF8);

  if(res!=0) {
    char errmsg[2048];
    regerror(res, &compiled_global_regexp, errmsg, 2048);
    wcerr<<"Regex '"<<global_regexp<<"' compilation error: "<<errmsg<<"\n";
    exit(EXIT_FAILURE);
  }

  regexp_was_compiled=true;
}

bool 
LexicalizedWords::is_lexicalized_word(wstring word) {
  int res=regexec(&compiled_global_regexp, 
		  UtfConverter::toUtf8(word).c_str(), 0, NULL, REG_UTF8);

  //cerr<<"Word: "<<word<<" is lexicalized? "<<(res==0)<<"\n";

  return (res==0); //true if regular exp. was matched
}

void
LexicalizedWords::destroy() {
  if (regexp_was_compiled)
    regfree(&compiled_global_regexp);
}

void
LexicalizedWords::copy(LexicalizedWords const &o) {
  lexicalized_words=o.lexicalized_words;
  global_regexp=o.global_regexp;
  regexp_was_compiled=o.regexp_was_compiled;

  if (regexp_was_compiled) 
    insert_ends();
}

LexicalizedWords& 
LexicalizedWords::operator =(LexicalizedWords const &o) {
  if(this != &o) {
    destroy();
    copy(o);
  }
  return *this;
}
