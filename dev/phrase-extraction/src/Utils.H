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
 
#ifndef __UTILS_H_
#define __UTILS_H_

#include <string>
#include <vector>
#include <apertium/utf_converter.h>

using namespace std;

class Utils {
  public:
  
  static wstring trim(wstring str);

  static vector<string> split_string(const string& input, const string& delimiter);

  static string vector2string(const vector<string>& v);

  //Replace each ocurrence of the string 'olds' by the string 'news' in string 'source'
  static string substitute(const string& source, const string& olds, const string& news);

  //Remove begin (^) and end mark ($)
  static wstring remove_begin_and_end_marks(wstring word);

  //Return the lemma of the word (including queue)
  //Begin (^) and end ($) marks must be removed before calling this method
  static wstring get_lemma(wstring word);

  //Return the lemma of the word (without queue)
  //Begin (^) and end ($) marks must be removed before calling this method
  static wstring get_lemma_without_queue(wstring word);

  //Return the queue of the word (if present)
  //Begin (^) and end ($) marks must be removed before calling this method
  static wstring get_queue(wstring word);


  //Return the tags of the word
  //Begin (^) and end ($) marks must be removed before calling this method
  static wstring get_tags(wstring word);

  //Return the first tag
  //tags must be obtained through the get_tags function
  static wstring get_first_tag(wstring tags);

  //Return which value on those given in values is present in string
  //tags, values must be of the form "m|f|mf"
  static wstring get_tag_value(wstring tags, wstring values);

  //Return true if 'word' is unknown
  //Begin (^) and end ($) marks must be removed before calling this method
  static bool is_unknown_word(wstring word);

  //Convert tags into the transfer format. 
  //Ex. of input: <n><m><sg>
  //Ex. of output: n.m.sg
  static wstring tags2transferformat(const wstring& tags);

  static wstring itoa(int n);
  
  static wstring ftoa(double f);

  static double wtod(wstring s);

  static long wtol(wstring s);

  static wstring strtolower(const wstring& s);

  static bool case_insensitive_equal(const wstring& a, const wstring& b);
};

#endif
