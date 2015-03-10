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


#include "AlignmentTemplate.H"
#include "Utils.H"
#include <apertium/string_utils.h>
#include <apertium/utf_converter.h>

#include <cstdlib>
#include <iostream>

LexicalizedWords AlignmentTemplate::source_lexicalized_words;
LexicalizedWords AlignmentTemplate::target_lexicalized_words;
bool AlignmentTemplate::keep_restrictions;
bool AlignmentTemplate::keep_restrictions_of_unaligned_too;

bool AlignmentTemplate::keep_lemmas;

AlignmentTemplate::AlignmentTemplate() {
  invalid=VALID;
}

AlignmentTemplate::AlignmentTemplate(wstring al):Alignment(al,5) {
  invalid=VALID;
  vector<wstring> v;

  v=StringUtils::split_wstring(al, L" | ");

  if (v.size()!=5) {
    wcerr<<L"Error in AlignmentTemplate::AlignmentTemplate when reading alignment template from string '"<<al<<L"'\n";
    wcerr<<L"Unexpected number of fields separated by ' | '\n";
    exit(EXIT_FAILURE); 
  }

  restrictions=StringUtils::split_wstring(v[4], L" ");
}

AlignmentTemplate::AlignmentTemplate(const AlignmentTemplate& al):Alignment(al) {
  invalid=al.invalid;
  restrictions=al.restrictions;
}
    
AlignmentTemplate::~AlignmentTemplate() {
}

void 
AlignmentTemplate::set_keeprestrictions(bool &keep)
{
	keep_restrictions=keep;
}

bool 
AlignmentTemplate::is_keeprestrictions()
{
	return keep_restrictions;
}

void 
AlignmentTemplate::set_keeprestrictionsofunalignedtoo(bool &keep)
{
	keep_restrictions_of_unaligned_too=keep;
}

bool 
AlignmentTemplate::is_keeprestrictionsofunalignedtoo()
{
	return keep_restrictions_of_unaligned_too;
}

void 
AlignmentTemplate::set_keeplemmas(bool &keep)
{
	keep_lemmas=keep;
}

bool 
AlignmentTemplate::is_keeplemmas()
{
	return keep_lemmas;
}

void 
AlignmentTemplate::set_count(int count) {
  score=(double)count;
}

int
AlignmentTemplate::get_count() {
  return (int) score;
}

bool
AlignmentTemplate::is_valid(bool equalcat, bool noword4word, FSTProcessor& fstp, Alignment& bilph) {

  if(invalid!=VALID)
    return false;

  //Now follows some additional validations

  //There cannot be INVALID restrictions
  for (unsigned i=0; i<restrictions.size(); i++) {
    if (restrictions[i]==L"__INVALID__") {
      invalid=INVALID_RESTRICTIONS;
      return false;
    }
  }

//TODO: fix!!!!!!!!!!!!!!!
  if (equalcat) {
    //Test that those open words that are aligned have the same
    //category, i. e., the same first tag
    for (unsigned i=0; i<source.size(); i++) {
      if (source[i][0]==L'<') { //It's an open word
	int j=get_open_target_word_pos(i);

	wstring first_sl_tag=Utils::get_first_tag(source[i]);
	wstring first_tl_tag=Utils::get_first_tag(target[j]);

	if (first_sl_tag!=first_tl_tag) {
	  invalid=INVALID_NO_EQUALCAT;
	  return false;
	}
      }
    }
  }

  if (noword4word) {
    if (is_equivalent_to_word_for_word(bilph, fstp)) {
      invalid=INVALID_EQUIVALENT_WORD_FOR_WORD;
      return false;
    }
  }

  invalid=VALID;
  return true;
}

int 
AlignmentTemplate::invalid_reason() {
  return invalid;
}

wstring
AlignmentTemplate::to_wstring() {
  Alignment &al=(*this);
  wstring s=al.to_wstring();

  s+=L" |";

  for(unsigned i=0; i<restrictions.size(); i++) 
    s+=L" "+restrictions[i];

  return s;
}

ostream& operator << (ostream& os, AlignmentTemplate& at) {
  wstring w=at.to_wstring();
  string s=UtfConverter::toUtf8(w);

  os<<s;
  return os;
}

wostream& operator << (wostream& os, AlignmentTemplate& at) {
  os<<at.to_wstring();
  return os;
  /*
  Alignment &al=at;
  os<<al<<" |";

  for(unsigned i=0; i<at.restrictions.size(); i++) 
    os<<" "<<at.restrictions[i];

  return os;
  */
}


void 
AlignmentTemplate::set_lexicalized_words(const LexicalizedWords& scw, const LexicalizedWords& tcw) {
  source_lexicalized_words=scw;
  target_lexicalized_words=tcw;

  source_lexicalized_words.insert_ends();
  target_lexicalized_words.insert_ends();
}

AlignmentTemplate 
AlignmentTemplate::xtract_alignment_template(Alignment& al, FSTProcessor& fstp) {
  AlignmentTemplate at;

  at.invalid=VALID;
  at.alignment=al.alignment;
  at.score=0;

  int nopen_source=0;
  int nopen_target=0;

  //Determine the word class for each source word
  for(unsigned i=0; i<al.source.size(); i++) {
    wstring w=Utils::remove_begin_and_end_marks(al.source[i]);
    wstring wclass;

    if (Utils::is_unknown_word(w))
      wclass=L"__UNKNOWN__";
    else if (source_lexicalized_words.is_lexicalized_word(w)) 
      wclass=w;
    else {
      wclass=Utils::get_tags(w);
      nopen_source++;
    }
    at.source.push_back(wclass);
  }

  //Determine the word class for each target word
  for(unsigned i=0; i<al.target.size(); i++) {
    wstring w=Utils::remove_begin_and_end_marks(al.target[i]);
    wstring wclass;

    if (Utils::is_unknown_word(w))
      wclass=L"__UNKNOWN__";
    else if (target_lexicalized_words.is_lexicalized_word(w))
      wclass=w;
    else {
      wclass=Utils::get_tags(w);
      nopen_target++;
    }
    at.target.push_back(wclass);
  }

  if (nopen_source!=nopen_target) {
    at.invalid=INVALID_WRONG_OPEN_WORDS;
    at.restrictions.push_back(L"__INVALID__");
    return at;
  }

  if (!at.are_open_word_aligments_ok()) {
    at.invalid=INVALID_WRONG_OPEN_WORDS;
    at.restrictions.push_back(L"__INVALID__");
    return at;
  }

  //Calculate the restricitions that need to be met
  //before applying this AT
  for(unsigned i=0; i<al.source.size(); i++) {
    wstring w=Utils::remove_begin_and_end_marks(al.source[i]);
    wstring biltrans, bclass;

    if (Utils::is_unknown_word(w)) 
      bclass=L"__UNKNOWN__";
    else if (source_lexicalized_words.is_lexicalized_word(w) && !is_keeprestrictions()) 
      bclass=L"__CLOSEWORD__";
    else {
	 
	 bool okTokeepRestriction=true;
	 bool tryingTokeepRestrictionOfLexicalisedWord=false;	
	 if(source_lexicalized_words.is_lexicalized_word(w) && is_keeprestrictions())
	 {
		 tryingTokeepRestrictionOfLexicalisedWord=true;
	 }
	  
		
      //We need to replace each "_" in w by a blank " " before translating
      w=StringUtils::substitute(w,L"_",L" ");

      biltrans=fstp.biltransWithoutQueue(w, false);

      if (!is_translation_ok(biltrans)) {
	if(tryingTokeepRestrictionOfLexicalisedWord)
		okTokeepRestriction=false;
	else
	{
	at.invalid=INVALID_NO_OK_TRANSLATIONS;
	wcerr<<L"Error in AlignmentTemplate::xtract_alignment_template: ";
	wcerr<<L"There were no OK translation for source word '"<<w<<"', translation was: '"<<biltrans<<L"'\n";
	at.restrictions.push_back(L"__INVALID__");
	return at;
	}
      } 

      //Execution continues only if ALL since this point was OK
      bclass=Utils::get_tags(biltrans);
      wstring blemma=Utils::get_lemma(biltrans);

      int tlp=-1;
      if(tryingTokeepRestrictionOfLexicalisedWord)
		tlp=at.get_target_word_pos(i);
      else
        tlp=at.get_open_target_word_pos(i);
      if (tlp>=0) {
	wstring tlemma=StringUtils::substitute(Utils::get_lemma(Utils::remove_begin_and_end_marks(al.target[tlp])),L"_",L" ");

	if (StringUtils::tolower(blemma) != StringUtils::tolower(tlemma)) {
	if(tryingTokeepRestrictionOfLexicalisedWord)
		okTokeepRestriction=false;
	else
	{
	  at.invalid=INVALID_DIFFERENT_TRANSLATIONS;
	  wcerr<<L"Warning: The AT extracted from the following alignment cannot be used.\n";
	  wcerr<<al<<L"\n";
	  wcerr<<L"Cause: translation of '"<<w<<L"' is '"<<blemma<<L"', but it should be '"<<tlemma<<L"'\n";
	  at.restrictions.push_back(L"__INVALID__");
	  return at;
    }
	}
      } else {
	if(tryingTokeepRestrictionOfLexicalisedWord)
		okTokeepRestriction=false;
	else
	{
		wcerr<<L"Warning: The AT extracted from the following alignment cannot be used.\n";
		wcerr<<al<<L"\n";
		wcerr<<"Cause: bug not solved\n";
		at.invalid=INVALID_OTHERS;
		at.restrictions.push_back(L"__INVALID__");
		return at;
	}
      }
      
      if(tryingTokeepRestrictionOfLexicalisedWord && !okTokeepRestriction && !is_keeprestrictionsofunalignedtoo())
		bclass=L"__CLOSEWORD__";
	  
	  //if word is not present in bilingual dictionary
	  if(bclass.size()==0)
	    bclass=L"__CLOSEWORD__";
            
    }
    
	at.restrictions.push_back(bclass);
  }

  if (is_keeplemmas())
  {
		//restore lemmas of open words
		for(int i=0; i< at.source.size(); i++)
			if(at.source[i]==Utils::get_tags(at.source[i]))
				at.source[i]= Utils::remove_begin_and_end_marks(al.source[i]);
		
		for(int i=0; i< at.target.size(); i++)
			if(at.target[i]==Utils::get_tags(at.target[i]))
				at.target[i]=Utils::remove_begin_and_end_marks(al.target[i]);
  }
  return at;
}

bool
AlignmentTemplate::is_translation_ok(wstring t) {
  return ((t.length()>0)&&(t[0]!=L'@'));
}

/* OLD, realmente testea que la aplicación del AT proporcione el
mismo resultado - VER!!!!!!!!!!
bool 
AlignmentTemplate::is_equivalent_to_word_for_word(Alignment& al, FSTProcessor& fstp) {
  wstring al_target=L"";
  wstring at_translation=L"";
  //cerr<<"AT: "<<to_string()<<"\n";
  //cerr<<"AL: "<<al<<"\n";
  for(unsigned i=0; i<target.size(); i++) {
    if (at_translation.length()>0)
      at_translation+=L" ";

    if (target[i]==L"__UNKNOWN__") {
      at_translation+=target[i];
      //cerr<<"Unknown word: "<<target[i]<<"\n";
    } else if (target[i][0]!=L'<') { //It's a close word we copy it as is
      at_translation+=L"^"+target[i]+L"$";
      //cerr<<"Close word: "<<target[i]<<"\n";
    }  else {
      int p=get_open_source_word_pos(i);
      wstring w=Utils::remove_begin_and_end_marks(al.source[p]);
      wstring t=fstp.biltrans(w, false);
      //cerr<<"Source: "<<al.source[p]<<" Target: "<<target[i]<<" Translation: "<<t<<"\n";
      at_translation+=L"^"+Utils::get_lemma(t)+target[i]+L"$";
    }
  }

  for(unsigned i=0; i<al.target.size(); i++) {
    if(al_target.length()>0)
      al_target+=L" ";
    if (Utils::is_unknown_word(Utils::remove_begin_and_end_marks(al.target[i])))
      al_target+=L"__UNKNOWN__";
    else
      al_target+=al.target[i];
  }

  at_translation=StringUtils::tolower(at_translation);
  al_target=StringUtils::tolower(al_target);

  //cerr<<"TRANSLATION: "<<at_translation<<"\n";
  //cerr<<"TL AL SIDE: "<<al_target<<"\n";
  //cerr<<"Equivalent to word4word: "<<(al_target==at_translation)<<"\n\n";
  return (al_target==at_translation);
}
*/

bool 
AlignmentTemplate::is_equivalent_to_word_for_word(Alignment& al, FSTProcessor& fstp) {
  wstring word4word=L"";
  wstring translation=L"";

  //cerr<<"AT: "<<to_string()<<"\n";
  //cerr<<"AL: "<<al<<"\n";

  //First compute the translation applying the AT
  for(unsigned i=0; i<target.size(); i++) {
    if (translation.length()>0)
      translation+=L" ";

    if (target[i]==L"__UNKNOWN__") {
      translation+=target[i];
    } else if (target[i][0]!=L'<') { //It's a close word we copy it as is
      translation+=L"^"+target[i]+L"$";
    }  else {
      int p=get_open_source_word_pos(i);
      wstring w=Utils::remove_begin_and_end_marks(al.source[p]);
      wstring t=fstp.biltrans(w, false);
      translation+=L"^"+Utils::get_lemma(t)+target[i]+L"$";
    }
  }

  //Now compute the word for word translation
  for(unsigned i=0; i<al.source.size(); i++) {
    if (word4word.length()>0)
      word4word+=L" ";
    wstring w=Utils::remove_begin_and_end_marks(al.source[i]);
    if (Utils::is_unknown_word(w))
      word4word+=L"__UNKNOWN__";
    else
      word4word+=L"^"+fstp.biltrans(w, false)+L"$";
  }


  translation=StringUtils::tolower(translation);
  word4word=StringUtils::tolower(word4word);

  //cerr<<"TRANSLATION: "<<translation<<"\n";
  //cerr<<"WORD4WORD: "<<word4word<<"\n";
  //cerr<<"Equivalent to word4word: "<<(translation==word4word)<<"\n\n";

  return (translation==word4word);
}

bool
AlignmentTemplate::are_open_word_aligments_ok() {

	
  bool open_sl[source.size()];
  bool open_tl[target.size()];

  for(unsigned i=0; i<source.size(); i++) {
    if ((source[i][0]==L'<')||(source[i]==L"__UNKNOWN__"))
      open_sl[i]=true;
    else
      open_sl[i]=false;
  }

  for(unsigned i=0; i<target.size(); i++) {
    if ((target[i][0]==L'<')||(target[i]==L"__UNKNOWN__"))
      open_tl[i]=true;
    else
      open_tl[i]=false;
  }

  //Each open SL word must be aligned with only one open TL word
  for (unsigned i=0; i<source.size(); i++) {
    if (open_sl[i]) {
      bool aligned=false;
      for (unsigned j=0; j<target.size(); j++) {
	if (open_tl[j]) {
	  if (alignment[i][j]) {
	    if (aligned)
	      return false;
	    aligned=true;
	  }
	}
      }
      if (!aligned)
	return false;
    }
  }

  //Each open TL word must be aligned with only one open SL word
  for (unsigned i=0; i<target.size(); i++) {
    if (open_tl[i]) {
      bool aligned=false;
      for (unsigned j=0; j<source.size(); j++) {
	if (open_sl[j]) {
	  if (alignment[j][i]) {
	    if (aligned)
	      return false;
	    aligned=true;
	  }
	}
      }
      if (!aligned)
	return false;
    }
  }

  return true;
}

int 
AlignmentTemplate::get_open_source_word_pos(int target_pos) {
  for (unsigned i=0; i<source.size(); i++) {
    if (((source[i][0]==L'<')||(source[i]==L"__UNKNOWN__")) && (alignment[i][target_pos]))
      return i;
  }

  wcerr<<L"Error in AlignmentTemplate::get_open_source_word_pos: No open source word aligned with target word at "<<target_pos<<L" was found\n";
  wcerr<<L"AT: "<<to_wstring()<<L"\n";
  exit(EXIT_FAILURE);

  return -1;
}

int 
AlignmentTemplate::get_first_open_source_word_pos(int target_pos) {
  for (unsigned i=0; i<source.size(); i++) {
    if (((source[i][0]==L'<')||(source[i]==L"__UNKNOWN__")) && (alignment[i][target_pos]))
      return i;
  }

  return get_source_word_pos(target_pos) ;
}

int 
AlignmentTemplate::get_source_word_pos(int target_pos) {
  for (unsigned i=0; i<source.size(); i++) {
    if (alignment[i][target_pos])
      return i;
  }

  wcerr<<L"Error in AlignmentTemplate::get_source_word_pos: No source word aligned with target word at "<<target_pos<<L" was found\n";
  wcerr<<L"AT: "<<to_wstring()<<L"\n";
  exit(EXIT_FAILURE);

  return -1;
}

int 
AlignmentTemplate::get_open_target_word_pos(int source_pos, bool exit_if_not_found) {
  for (unsigned i=0; i<target.size(); i++) {
    if (((target[i][0]==L'<')||(target[i]==L"__UNKNOWN__")) && (alignment[source_pos][i]))
      return i;
  }

  if (exit_if_not_found)
  {
	  wcerr<<L"Error in AlignmentTemplate::get_open_target_word_pos: No open target word aligned with source word at "<<source_pos<<L" was found\n";
	  wcerr<<L"AT: "<<to_wstring()<<L"\n";
	  exit(EXIT_FAILURE);
  }

  return -1;
}

int 
AlignmentTemplate::get_target_word_pos(int source_pos) {
  for (unsigned i=0; i<target.size(); i++) {
    if  (alignment[source_pos][i])
      return i;
  }

  return -1;
}
