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
 
#ifndef __ALIGNMENTTEMPLATE_H_
#define __ALIGNMENTTEMPLATE_H_

using namespace std;

#include <vector>
#include <string>
#include <iostream>
#include <map>
#include <set>
#include <lttoolbox/fst_processor.h>

#include "Alignment.H"
#include "LexicalizedWords.H"


class AlignmentTemplate:public Alignment {
private:
  vector<wstring> restrictions;
  int invalid; //While extracting the AT this flag is modified

  static LexicalizedWords source_lexicalized_words;
  static LexicalizedWords target_lexicalized_words;

  //Return true if the translation 't' is ok
  static bool is_translation_ok(wstring t);
  
  static bool keep_restrictions;
  static bool keep_restrictions_of_unaligned_too;
  static bool keep_lemmas;
  

public: 

  //Set of constant to identify why an AT is discarded (invalid)
  static const int VALID = 0;
  static const int INVALID_WRONG_OPEN_WORDS = 1;       
  static const int INVALID_NO_OK_TRANSLATIONS = 2;
  static const int INVALID_DIFFERENT_TRANSLATIONS = 3;
  static const int INVALID_RESTRICTIONS = 4;
  static const int INVALID_NO_EQUALCAT = 5;
  static const int INVALID_EQUIVALENT_WORD_FOR_WORD = 6;
  static const int INVALID_OTHERS = 7;

  AlignmentTemplate();

  AlignmentTemplate(wstring al);

  AlignmentTemplate(const AlignmentTemplate& al);
    
  ~AlignmentTemplate();

  /** Use to set the number of times this AT occurs */
  void set_count(int count);

  int get_count();

  /** Test whether this AT is valid, i. e. it is suitable to be used
   * within the apertium machine translation system.
   * if 'equalcat' is true the first tag of aligned (open) words must be
   * the same
   */
  bool is_valid(bool equalcat, bool noword4word, FSTProcessor &fstp, Alignment &bilph);

  int invalid_reason();

  /** Test whether the alignments between open words in source and
   * target language are ok, i.e., all source open words are aligned
   * with only one target open word, and vice versa.
   */
  bool are_open_word_aligments_ok();

  /** This method returns the position of the open source word that is
   * aligned with the open target word received as a parameter
   * NOTE: It is supposed that ONLY one open source word is aligned
   * with each open target word.
   */
  int get_open_source_word_pos(int target_pos);
  
  int get_first_open_source_word_pos(int target_pos);
  
  int get_source_word_pos(int target_pos);

  /** This method returns the position of the open target word that is
   * aligned with the open source word received as a parameter
   * NOTE: It is supposed that ONLY one open target word is aligned
   * with each open source word.
   */
  int get_open_target_word_pos(int source_pos,bool exit_if_not_found=true);
  
  int get_target_word_pos(int source_pos);

  /** Test if the alignment template performs no transformation, i.e.,
   *  it is equivalent to word-for-word translation.
   *  NOTE: It is supposed that the Alignment received as input
   *  matches the SL part of the AT and the restrictions.
   */
  bool is_equivalent_to_word_for_word(Alignment& al, FSTProcessor& fstp);

  wstring to_wstring();

  static void set_lexicalized_words(const LexicalizedWords& scw, const LexicalizedWords& tcw);
  
  static AlignmentTemplate xtract_alignment_template(Alignment& al, FSTProcessor& fstp);
  
  static void set_keeprestrictions(bool &keep);
  static bool is_keeprestrictions();
  
  static void set_keeprestrictionsofunalignedtoo(bool &keep);
  static bool is_keeprestrictionsofunalignedtoo();
  
  static void set_keeplemmas(bool &keep);
  static bool is_keeplemmas();

  friend ostream& operator << (ostream& os, AlignmentTemplate& at);

  friend wostream& operator << (wostream& os, AlignmentTemplate& at);

  friend class TransferRule;
  
  friend class AlignmentTemplateGreaterThanByCount;

  //friend class AlignmentTemplateLessThan;
};


//Definition of the compare function used to sort the
//alignment templates by their counts
class AlignmentTemplateGreaterThanByCount {
public:
  bool operator()(const AlignmentTemplate &at1, const AlignmentTemplate &at2)  const {
    return (at1.score>at2.score);
  }
};

/*
//Definition of the compare function used to sort the
//alignment templates
class AlignmentTemplateLessThan {
public:
  bool operator()(const AlignmentTemplate &at1, const AlignmentTemplate &at2)  const {
    //True if at1 is less than at2

    if (at1.source.size()<at2.source.size()) 
      return true;
    else if (at1.source.size()>at2.source.size()) 
      return false;
    

    if (at1.target.size()<at2.target.size()) 
      return true;
    else if (at1.target.size()>at2.target.size()) 
      return false;

    
    if (at1.restrictions.size()<at2.restrictions.size()) 
      return true;
    else if (at1.restrictions.size()>at2.restrictions.size()) 
      return false;
    

    if (at1.alignment<at2.alignment) 
      return true;
    else if (at1.alignment>at2.alignment) 
      return false;
    

    for (unsigned i=0; i<at1.source.size(); i++) {
      if (at1.source[i]<at2.source[i]) 
	return true;
      else if (at1.source[i]>at2.source[i]) 
	return false;
    }

    for (unsigned i=0; i<at1.target.size(); i++) {
      if (at1.target[i]<at2.target[i])
	return true;
      else if (at1.target[i]>at2.target[i])
	return false;
    }

    for (unsigned i=0; i<at1.restrictions.size(); i++) {
      if (at1.restrictions[i]<at2.restrictions[i]) 
	return true;
      else if (at1.restrictions[i]>at2.restrictions[i]) 
	return false;
    }

    return false;
  }
};
*/

#endif
