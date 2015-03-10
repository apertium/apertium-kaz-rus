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


#ifndef __LEXICALIZEDWORDS_H_
#define __LEXICALIZEDWORDS_H_


#include <set>
#include <string>
#include <iostream>
#include <map>

#include <pcreposix.h>

#define TAGS   L"((<[a-zA-Z0-9]+>)+)"

using namespace std;

class LexicalizedWords {
private:
  //set with all lexicalized words (first is the 'lemma' and second is the 'tags')
  set<pair<wstring, wstring> > lexicalized_words;

  wstring global_regexp;
  regex_t compiled_global_regexp;

  bool regexp_was_compiled;

  void destroy();

  void copy(LexicalizedWords const &o);

public: 
       
  LexicalizedWords();

  LexicalizedWords(const LexicalizedWords& cw);
    
  ~LexicalizedWords();

  void insert(wstring lemma, wstring tags);

  bool is_lexicalized_word(wstring word);

  /** The insertion of lexicalized words has finish. No more close
   *  lexicalized will added.
   */
  void insert_ends();

  LexicalizedWords & operator =(LexicalizedWords const &o);
};

#endif
