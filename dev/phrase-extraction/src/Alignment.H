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
 
#ifndef __ALIGNMENT_H_
#define __ALIGNMENT_H_

using namespace std;

#include <vector>
#include <string>
#include <iostream>
#include <map>
#include <set>

class Alignment {
protected:
  double score;
  vector<wstring> source;
  vector<wstring> target;

  //Matrix source.size x target.size with the alignments
  map<int, map<int, bool> > alignment;

  //True if the elements in SP are consecutive
  bool consecutive(const set<int>& SP);

  //True if the elements words in the interval are not aligned to words outside it
  bool consistent(int from_source, int to_source, int from_target, int to_target);

  //Return an alignment that is extracted from this one (*this)
  Alignment sub_alignment(int from_source, int to_source, int from_target, int to_target);

  //True if source size and the target size of both alignments (*this
  //and al2) are equal
  bool are_the_same_alignment(const Alignment& al2);
  
  static vector<wstring> marker_categories;
public: 
       
  Alignment();

  Alignment(wstring al, int nfields=4);

  Alignment(const Alignment& al);
    
  ~Alignment();

  vector<Alignment> extract_bilingual_phrases(int min_length, int max_length, int marker=-1);

  int get_source_length();

  int get_target_length();

  void set_score(double p_score);
  
  int length();

  wstring to_wstring();

  //(*this) becomes the intersected alignment
  bool intersection(Alignment& al2);

  //(*this) becomes the united alignment
  bool unionn(Alignment& al2);

  //(*this) becomes the refined intersected alignment
  bool refined_intersection(Alignment& al2);

  //True if all source words are aligned with at least one target
  //word, and vice versa
  bool allwords_aligned();

  //True if the first source word and the last source word are aligned 
  //with at least one target word and vice versa
  bool all_end_words_aligned();
  
  static void set_marker_categories(const vector<wstring> v);
  
  friend ostream& operator << (ostream& os, Alignment& al);

  friend wostream& operator << (wostream& os, Alignment& al);

  friend class AlignmentTemplate;
};

#endif
