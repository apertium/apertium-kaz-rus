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
 
#ifndef __TRANSFER_RULE_H_
#define __TRANSFER_RULE_H_

using namespace std;

#include <vector>
#include <string>
#include <iostream>
#include <set>
#include <map>

#include "AlignmentTemplate.H"

class TransferRule {
private:
  vector<AlignmentTemplate> ats;
  wstring source;

  //To store different categories used by the automatically generated
  //rules. It is update when the add_alignment_template method is
  //called 
  //first=lemma; second=tags;
  static set<pair<wstring, wstring> > categories;

  //To store the attributes of the categories used by the
  //automatically generated rules. It is update when the
  //add_alignment_template method is called
  static map<wstring,pair<set<wstring>, set<wstring> > > attributes;

  static wstring category_name(const wstring& lemma, const wstring& tags);
  
  static wstring escape_attr(const wstring attrstr);
  
  static wstring attribute_pos_group_name(const wstring& pos);

  static bool using_explicit_empty_tags;

  static bool sm_generalise;
  
  static bool provided_patterns;
  
  static bool no_vars_determined;
  
  static bool one_pattern_per_rule;
  
  static bool no_double_check_restrictions;
  
  static bool use_discard_rule;
  
  static bool generate_chunks;
  
  static bool empty_restrictions_match_everything;

  static int rule_counter;
  
  int rule_id;
public: 
       
  TransferRule();
  
  TransferRule(const TransferRule& al);
    
  ~TransferRule();

  /** Return true if the AT was added.
   */
  bool add_alignment_template(const AlignmentTemplate& at, vector<wstring> *pattern=NULL);
  
  int get_number_alignment_templates();
  
  wstring gen_apertium_transfer_rule(bool debug=false);

  static wstring gen_apertium_transfer_head(bool debug=false);

  static wstring gen_apertium_transfer_foot(bool debug=false);
  
  static int load_attributes(istream*);
  
  static wstring get_attribute_for_tag(wstring&, wstring&);
  
  static void remove_generalised_tags(wstring &);
  
  static void remove_final_asterisk(wstring &);
  
  static vector<wstring> extract_attribute_names(wstring &);
  
  static void set_using_explicit_empty_tags(bool f);
  
  static void set_generalise(bool f);
  
  static void set_provided_patterns(bool f);
  
  static void set_novarsdetermined(bool f);
  
  static void set_onepatternperrule(bool f);
  
  static void set_generate_chunks(bool f);
  
  static void set_no_double_check_restrictions(bool f);
  
  static void set_use_discard_rule(bool f);
  
  static void set_empty_restrictions_match_everything(bool f);
};

#endif
