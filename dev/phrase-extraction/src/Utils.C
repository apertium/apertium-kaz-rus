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

#include "Utils.H"

#include <iostream>
#include <lttoolbox/xml_parse_util.h>
#include <apertium/string_utils.h>
#include <stdio.h>

//Delete white spaces from the end and the begining of the string
wstring 
Utils::trim(wstring str) { 
  wstring::iterator it;
  
  while ((str.length()>0)&&((*(it=str.begin()))==L' ')) {
     str.erase(it);
  }
  
  while ((str.length()>0)&&((*(it=(str.end()-1)))==L' ')) {
     str.erase(it);
  }

  return str;
}

vector<string>
Utils::split_string(const string& input, const string& delimiter) {
  int pos;
  int new_pos;
  vector<string> result;
  string s="";
  pos=0;

  while (pos<(int)input.size()) {
    new_pos=input.find(delimiter, pos);
    if(new_pos<0)
      new_pos=input.size();
    s=input.substr(pos, new_pos-pos);
    if (s.length()==0) {
      cerr<<"Warning in Utils::split_string: After splitting there is an empty string\n";
      cerr<<"Skipping this empty string\n";
    } else
      result.push_back(s);
    pos=new_pos+delimiter.size();
    //pos=new_pos+1;
  }
  return result;
}


string 
Utils::vector2string(const vector<string>& v) {
  string s="";
  for(unsigned i=0; i<v.size(); i++) {
    if (i>0)
      s+=" ";
    s+=v[i];
  }
  return s;
}

string 
Utils::substitute(const string& source, const string& olds, const string& news) {
  string s=source;

  int p=s.find(olds,0);
  while (p!=(int)string::npos) {
    s.replace(p, olds.length(), news);
    p+=news.length();
    p=s.find(olds,p);
  }

  return s;
}


wstring 
Utils::remove_begin_and_end_marks(wstring word) {
  return word.substr(1, word.size()-2);
}

wstring
Utils::get_lemma(wstring word) {
  wstring s=L"";

  wstring::size_type p=word.find(L"<",0);
  if (p!=wstring::npos)
    s=word.substr(0, p);

  return s;
}

wstring 
Utils::get_lemma_without_queue(wstring word) {
  wstring l=get_lemma(word);
  wstring s=l;

  wstring::size_type p=l.find(L"#",0);
  if (p!=wstring::npos)
    s=l.substr(0, p);

  return s;
}

wstring 
Utils::get_queue(wstring word) {
  wstring l=get_lemma(word);
  wstring s=L"";

  wstring::size_type p=l.find(L"#",0);
  if (p!=wstring::npos)
    s=l.substr(p);

  return s;
}

wstring
Utils::get_tags(wstring word) {
  wstring::size_type p=word.find(L"<",0);
  if (p!=wstring::npos)
    return word.substr(p, word.size()-p);
  else //Unknown word, no tags for it
    return L"";
}

wstring
Utils::get_first_tag(wstring tags) {
  int p=tags.find(L">",0);
  return tags.substr(0,p+1);
}

bool 
Utils::is_unknown_word(wstring word) {
  return ((word.length()>0)&&(word[0]==L'*'));
}

wstring 
Utils::tags2transferformat(const wstring& tags) {
  wstring s;
  s=StringUtils::substitute(tags,L"><",L".");
  s=StringUtils::substitute(s,L"<",L"");
  s=StringUtils::substitute(s,L">",L"");

  return s;
}

wstring
Utils::itoa(int n) {
  char str[32];
  sprintf(str, "%d",n);
  return UtfConverter::fromUtf8(str);
}

wstring
Utils::ftoa(double f) {
  char str[32];
  sprintf(str, "%f",f);
  return UtfConverter::fromUtf8(str);
}

double
Utils::wtod(wstring s)
{
  return wcstod (s.c_str(), 0);
}

long
Utils::wtol(wstring s)
{
  return wcstol (s.c_str(), 0, 0);
} 

wstring 
Utils::get_tag_value(wstring tags, wstring values) {
  vector<wstring> pval=StringUtils::split_wstring(values,L"|");

  for(wstring::size_type i=0; i<pval.size(); i++) {
    if (tags.find(pval[i]) != wstring::npos)
    {
		int pos=tags.find(pval[i]);
		if( (pos==0 || tags[pos-1]==L'.') && (pos==tags.size()-1 || tags[pos+1]==L'.'))
			return pval[i];
		else
			return L"";
    }
  }

  return L"";
}

bool 
Utils::case_insensitive_equal(const wstring& a, const wstring& b) {
  wstring alower=L"";
  wstring blower=L"";

  for(unsigned i=0; i<a.length(); i++) {
    alower+=(wchar_t) towlower(a[i]);
  }

  for(unsigned i=0; i<b.length(); i++) {
    blower+=(wchar_t) towlower(b[i]);
  }

  return (alower==blower);
}

wstring
Utils::strtolower(const wstring& s) {
  wstring l=L"";
  for(unsigned i=0; i<s.length(); i++)
    l+=(wchar_t) towlower(s[i]);
  return l;
}

