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


#include "TransferRule.H"
#include "Utils.H"
#include <apertium/string_utils.h>
#include <algorithm>
#include <clocale>
#include <locale>
#include <utility>

set<pair<wstring, wstring> > TransferRule::categories;
map<wstring,pair< set<wstring>, set<wstring> > > TransferRule::attributes;
int TransferRule::rule_counter=0;

//Alignment templates contain explicit empty tags:
//Some additional checks are done in rules
bool TransferRule::using_explicit_empty_tags=false;

//Pattern is first tag of each word
bool TransferRule::sm_generalise=false;

//Don't use global vars to estimate value of GD and ND
bool TransferRule::no_vars_determined=false;

//Patterns are provided in the input. Alignment templates
//with different left sides may be grouped in the same rule
bool TransferRule::provided_patterns=false;

//only check queue=yes, enable it if dictionary restrictions are clean
bool TransferRule::no_double_check_restrictions=false;

//useless
bool TransferRule::one_pattern_per_rule=false;

//use new instruction to go back
bool TransferRule::use_discard_rule=false;

bool TransferRule::empty_restrictions_match_everything=false;

bool TransferRule::generate_chunks=false;

TransferRule::TransferRule() {
  source=L"";
  rule_id=rule_counter;
  rule_counter++;
}
  
TransferRule::TransferRule(const TransferRule& tr) {
  source=tr.source;
  ats=tr.ats;
}
    
TransferRule::~TransferRule() {
}

void 
TransferRule::set_using_explicit_empty_tags(bool f)
{
	using_explicit_empty_tags=f;
}

void
TransferRule::set_generate_chunks(bool f)
{
    generate_chunks=f;
}

void
TransferRule::set_generalise(bool f)
{
	sm_generalise=f;
}

void 
TransferRule::set_onepatternperrule(bool f)
{
	one_pattern_per_rule=f;
}

void 
TransferRule::set_novarsdetermined(bool f)
{
	no_vars_determined=f;
}

void 
TransferRule::set_provided_patterns(bool f)
{
	provided_patterns=f;
}

void 
TransferRule::set_no_double_check_restrictions(bool f)
{
	no_double_check_restrictions=f;
}

void
TransferRule::set_use_discard_rule(bool f)
{
	use_discard_rule=f;
}

void
TransferRule::set_empty_restrictions_match_everything(bool f)
{
	empty_restrictions_match_everything=f;
}



bool 
TransferRule::add_alignment_template(const AlignmentTemplate& at, vector<wstring> *pattern) {
  
  wstring source_at=L"";
  if(sm_generalise)
  {
	  for (unsigned i=0; i<at.source.size(); i++) {
		wstring s=at.source[i];
		if (source_at.size() > 0)
			source_at+=L" ";
		source_at+=Utils::get_first_tag(Utils::get_tags(s));
	   }
  }
  else
  {
	 if (provided_patterns)
		source_at=StringUtils::vector2wstring(*pattern);
	 else
		source_at=StringUtils::vector2wstring(at.source);
  }
  if (source.length()==0)
    source=source_at;

  if (source!=source_at)
    return false;

  ats.push_back(at);

   vector<wstring> source_for_categories=at.source;
   if(provided_patterns)
	source_for_categories=*pattern;
   
  //Now we revise the categories and the attributes that will be used
  //by the generated rules
  for (unsigned i=0; i<source_for_categories.size(); i++) {
    wstring s=source_for_categories[i];
    if (s.length()==0) {
      cerr<<"Error in TransferRule::add_alignment_template: an empty source word was found\n";
      exit(EXIT_FAILURE);
    }
    pair<wstring, wstring> cat;

    wstring tags=Utils::tags2transferformat(Utils::get_tags(s));
    
    if(sm_generalise)
    {
		//category is only first tag
		cat.first=L"";
		wstring tmpstr=Utils::get_first_tag(Utils::get_tags(s)).substr(1);
		cat.second=tmpstr.substr(0,tmpstr.size()-1)+L".*";
		//cat.second=tmpstr.substr(0,tmpstr.size()-1);
	}
	else
	{
		cat.first=Utils::get_lemma(s);
		//In case of generalised alignment templates, remove all the generalised tags, and leave only a '*'
		remove_generalised_tags(tags);
		cat.second=tags;
	}
	categories.insert(cat);
	//attributes.insert(tags);
	
  }

  return true;
}
  
int 
TransferRule::get_number_alignment_templates() {
  return ats.size();
}
  
wstring 
TransferRule::gen_apertium_transfer_rule(bool debug) {

  locale loc(setlocale(LC_ALL,""));	
 
  wstring rule=L"";
  bool include_otherwise=true;

  if (ats.size()==0) {
    cerr<<"Error in TransferRule::gen_apertium_transfer_rule: No alignment templates available\n";
    exit(EXIT_FAILURE);
  }

  //Sort the AT so as to apply always the most frequent AT that
  //satisfies the restrictions
  AlignmentTemplateGreaterThanByCount atcomparer;
  sort(ats.begin(), ats.end(), atcomparer);

  //debug
  //cerr<<"ats.size(): "<<ats.size()<<endl;

  rule+=L"<rule>\n";

  //The pattern to detect is the same for all AT within this transfer rule
  rule+=L"  <pattern>\n";
  wstring chunkName=L"";
  
  vector<wstring> generalpattern=StringUtils::split_wstring(source,L" ");
  
  //for(unsigned i=0; i<ats[0].source.size(); i++) {
	
  for(unsigned i=0; i<generalpattern.size(); i++) {
    wstring lemma=Utils::get_lemma(generalpattern[i]);
    wstring tags=Utils::tags2transferformat(Utils::get_tags(generalpattern[i]));
    wstring tagsnogen=tags;
    remove_generalised_tags(tagsnogen);   
    
    chunkName+=L"__";
    if(sm_generalise)
    {
		wstring tmpstr=Utils::get_first_tag(Utils::get_tags(generalpattern[i])).substr(1);
		rule+=L"    <pattern-item n=\"CAT__"+category_name(L"",tmpstr.substr(0,tmpstr.size()-1)+L".*")+L"\"/>\n";
		chunkName+=category_name(L"",tmpstr.substr(0,tmpstr.size()-1)+L".*");
	}
	else
	{
		rule+=L"    <pattern-item n=\"CAT__"+category_name(lemma,tagsnogen)+L"\"/>\n";
		chunkName+=category_name(lemma,tagsnogen);
	}
    
  }
  rule+=L"  </pattern>\n";

  rule+=L"  <action>\n";
  rule+=L"    <choose>\n";




  //There is a set of different actions depending on the TL side of
  //each AT. Consequently, there's one <when> statement per AT 
  for(unsigned i=0; i<ats.size(); i++) {
    rule+=L"      <when>";
    rule+=L"<!--"+ats[i].to_wstring()+L"-->\n";
    rule+=L"        <test>\n";

    int nconditions=0;
    wstring teststr=L"";
	
    
    //This AT can be applied if all restrictions are met
    for(unsigned j=0; j<ats[i].restrictions.size(); j++){
	
      if (ats[i].restrictions[j]!=L"__CLOSEWORD__") {
		  
	nconditions++;
	
	teststr+=L"          <or>\n";
	if (empty_restrictions_match_everything)
	{
	    wstring source_tags_transfer_format=Utils::tags2transferformat(Utils::get_tags(ats[i].source[j]));
	    remove_generalised_tags(source_tags_transfer_format);
	    remove_final_asterisk(source_tags_transfer_format);
	    vector<wstring> nongenTags=StringUtils::split_wstring(source_tags_transfer_format,L".");
	    
	    teststr+=L"           <and>\n";	
	    teststr+=L"            <begins-with>\n";
	    teststr+=L"              <clip pos=\""+Utils::itoa(j+1)+L"\" side=\"tl\" part=\"tags\" />\n";
	    teststr+=L"              <lit-tag v=\""+escape_attr(StringUtils::split_wstring(Utils::tags2transferformat(ats[i].restrictions[j]),L".")[0])+L"\"/>\n";
	    teststr+=L"            </begins-with>\n";
	    
	    vector<wstring> resTags=StringUtils::split_wstring(Utils::tags2transferformat(ats[i].restrictions[j]),L".");
	    wstring partofspeech=resTags[0];
	    
	    for (unsigned k=1 ; k<resTags.size(); k++)
	    {
		wstring tag=resTags[k];
		if(tag[0]==L'['){
		  wstring attr=tag.substr(1);
		  teststr+=L"               <equal>\n";
		  teststr+=L"                 <clip pos=\""+Utils::itoa(j+1)+L"\" side=\"tl\" part=\"learned_"+attr+L"\"/>\n";
		  teststr+=L"                 <clip pos=\""+Utils::itoa(j+1)+L"\" side=\"sl\" part=\"learned_"+attr+L"\"/>\n";
		  teststr+=L"               </equal>\n";
		}
		else if(tag[0]==L']'){
		  wstring attr=tag.substr(1);
		  teststr+=L"               <not><equal>\n";
		  teststr+=L"                 <clip pos=\""+Utils::itoa(j+1)+L"\" side=\"tl\" part=\"learned_"+attr+L"\"/>\n";
		  teststr+=L"                 <clip pos=\""+Utils::itoa(j+1)+L"\" side=\"sl\" part=\"learned_"+attr+L"\"/>\n";
		  teststr+=L"               </equal></not>\n";
		}
		else{
		  wstring attr=get_attribute_for_tag(tag,partofspeech);
		  //teststr+=L"               <or>\n";
		  teststr+=L"               <equal>\n";
		  teststr+=L"                 <clip pos=\""+Utils::itoa(j+1)+L"\" side=\"tl\" part=\""+attr+L"\"/>\n";
		  if(tag.size() >= 10 && tag.substr(0,10)==L"empty_tag_" )
			teststr+=L"                 <lit v=\"\"/>\n";
		  else
			teststr+=L"                 <lit-tag v=\""+escape_attr(tag)+L"\"/>\n";
			
		  teststr+=L"               </equal>\n";
		  //Not necessary anymore
		  //A restriction with the same value that the sl tag may also mean that the tag dissappears (e.g., genders in es-en)
		  //if(std::find(nongenTags.begin(), nongenTags.end(), tag) != nongenTags.end()) {
		    //teststr+=L"               <equal>\n";
		    //teststr+=L"                 <clip pos=\""+Utils::itoa(j+1)+L"\" side=\"tl\" part=\""+attr+L"\"/>\n";
		    //teststr+=L"                 <lit v=\"\"/>\n";
		    //teststr+=L"               </equal>\n";
		  //}  
		  //teststr+=L"               </or>\n";
		}
	    }
	    
	    teststr+=L"           </and>\n";	
	}
	else
	{
	teststr+=L"            <equal>\n";
	teststr+=L"              <clip pos=\""+Utils::itoa(j+1)+L"\" side=\"tl\" part=\"tags\" queue=\"no\"/>\n";
	teststr+=L"              <lit-tag v=\""+escape_attr(Utils::tags2transferformat(ats[i].restrictions[j]))+L"\"/>\n";
	teststr+=L"            </equal>\n";
	}

 
	int targetWordPos=ats[i].get_open_target_word_pos(j,false);
	
	if(targetWordPos!=-1)
	{
	
	wstring target_transfer_format=Utils::tags2transferformat(Utils::get_tags(ats[i].target[targetWordPos]));
	
	bool isGeneralised=false;
	for(int myi=0; myi<target_transfer_format.size(); myi++)
    {
		if(target_transfer_format[myi] == L'*')
		{
			target_transfer_format=target_transfer_format.substr(0,myi-1);
			isGeneralised=true;
			break;
		}
	} 
	
	if(!isGeneralised){
		if(!no_double_check_restrictions)
		{
			teststr+=L"            <equal>\n";
			teststr+=L"              <clip pos=\""+Utils::itoa(j+1)+L"\" side=\"tl\" part=\"tags\" queue=\"yes\"/>\n";
			teststr+=L"              <lit-tag v=\""+escape_attr(target_transfer_format)+L"\"/>\n";
			teststr+=L"            </equal>\n";
		}
	}
	else{
				
		vector<wstring> tltags=StringUtils::split_wstring(target_transfer_format,L".");
		wstring partofspeech=tltags[0];
		tltags.erase(tltags.begin());
		
		vector<wstring> tlattrs;
		for(vector<wstring>::iterator it=tltags.begin(); it!=tltags.end(); ++it){
			wstring attribute=get_attribute_for_tag((*it),*(tltags.begin()));
			tlattrs.push_back(attribute);
		}
		
		if(!no_double_check_restrictions)
		{
		
			if(tltags.size() > 0)
				teststr+=L"            <and>\n";
			
			if(attributes.find(attribute_pos_group_name(partofspeech))==attributes.end())
			{
				pair<wstring,pair<set<wstring>, set<wstring> > > newelement;
				newelement.first=attribute_pos_group_name(partofspeech);
				pair<set<wstring>, wstring> newelementvalue;
				newelementvalue.first.insert(partofspeech);
				//newelementvalue.second=L"";
				attributes.insert(newelement);
			}
			
			teststr+=L"               <equal>\n";
			teststr+=L"                 <clip pos=\""+Utils::itoa(j+1)+L"\" side=\"tl\" part=\""+attribute_pos_group_name(partofspeech)+L"\"/>\n";
			teststr+=L"                 <lit-tag v=\""+partofspeech+L"\"/>\n";
			teststr+=L"               </equal>\n";
			
			for(int vcounter=0; vcounter < tltags.size(); vcounter++){
				teststr+=L"               <equal>\n";
				teststr+=L"                 <clip pos=\""+Utils::itoa(j+1)+L"\" side=\"tl\" part=\""+tlattrs[vcounter]+L"\"/>\n";
				teststr+=L"                 <lit-tag v=\""+escape_attr(tltags[vcounter])+L"\"/>\n";
				teststr+=L"               </equal>\n";
			}
			if(tltags.size() > 0)
				teststr+=L"            </and>\n";
		}
		
	}
	
	}

	teststr+=L"          </or>\n";
      }
      
      //If we are working with generalised ATs, check also SL side, as
      //ATs with different left side may be grouped in the same rule
      if(sm_generalise || provided_patterns || using_explicit_empty_tags)
      {
		  wstring source_tags_transfer_format=Utils::tags2transferformat(Utils::get_tags(ats[i].source[j]));
		  wstring source_lemma=Utils::get_lemma(ats[i].source[j]);
		  
		  if(source_lemma.size() > 0 && (sm_generalise || provided_patterns))
		  {
			nconditions++;
			teststr+=L"            <or>";
			
			teststr+=L"            <equal>\n";
			teststr+=L"              <clip pos=\""+Utils::itoa(j+1)+L"\" side=\"sl\" part=\"lem\" />\n";
			teststr+=L"              <lit v=\""+StringUtils::substitute(source_lemma,L"_",L" ")+L"\"/>\n";
			teststr+=L"            </equal>\n";
			
			teststr+=L"            <equal>\n";
			teststr+=L"              <clip pos=\""+Utils::itoa(j+1)+L"\" side=\"sl\" part=\"lem\" />\n";
			teststr+=L"              <lit v=\"";
			teststr+=toupper<wchar_t>(StringUtils::substitute(source_lemma,L"_",L" ")[0],loc);
			teststr+=StringUtils::substitute(source_lemma,L"_",L" ").substr(1)+L"\"/>\n";
			teststr+=L"            </equal>\n";
			
			teststr+=L"            </or>\n";
			
		  }
		  
		  vector<wstring> alltags=StringUtils::split_wstring(source_tags_transfer_format,L".");
		  remove_generalised_tags(source_tags_transfer_format);
		  remove_final_asterisk(source_tags_transfer_format);
		  vector<wstring> nongenTags=StringUtils::split_wstring(source_tags_transfer_format,L".");
		  
		  
		  for(int tagi=1; tagi<nongenTags.size(); tagi++)
		  {
			if( !(nongenTags[tagi].size()>=3 &&  nongenTags[tagi].substr(0,3)==L"RES") )
			{
			nconditions++;
			teststr+=L"            <equal>\n";
			teststr+=L"              <clip pos=\""+Utils::itoa(j+1)+L"\" side=\"sl\" part=\""+get_attribute_for_tag(nongenTags[tagi],nongenTags[0])+L"\" />\n";
			if(nongenTags[tagi].size() >= 10 && nongenTags[tagi].substr(0,10)==L"empty_tag_" )
				teststr+=L"              <lit v=\"\"/>\n";
			else
				teststr+=L"              <lit-tag v=\""+escape_attr(nongenTags[tagi])+L"\"/>\n";
			teststr+=L"            </equal>\n";
			}
		  }
		  
		  //I think this chunk of code should be removed anyway but...
		  if (!empty_restrictions_match_everything)
		    for(int tagi=1; tagi<alltags.size(); tagi++)
		    {
			    wstring tag=alltags[tagi];
			    if(tag.size()>0 && tag[0]==L'*')
			    {
				  nconditions++;
			      teststr+=L"            <equal>\n";
				  teststr+=L"              <clip pos=\""+Utils::itoa(j+1)+L"\" side=\"sl\" part=\"learned_"+tag.substr(1)+L"\" />\n";
				  teststr+=L"              <clip pos=\""+Utils::itoa(j+1)+L"\" side=\"tl\" part=\"learned_"+tag.substr(1)+L"\" />\n";
				  teststr+=L"            </equal>\n";
				  
			    }
		    }
	  }
      
    }
    
	

    if (nconditions==0) { //All words were close words. We introduce a
			  //condition that is always true
      teststr+=L"          <equal>\n";
      teststr+=L"            <lit v=\"TRUE\"/>\n";
      teststr+=L"            <lit v=\"TRUE\"/>\n";
      teststr+=L"          </equal>\n";
      //LO COMENTO PARA QUE MIS SCRIPTS DE DEPURACION FUNCIONEN BIEN
      //include_otherwise=false;
    }

    if (nconditions>1) // There are more than one restriction to test
      rule+=L"        <and>\n";

    rule+=teststr;

    if (nconditions>1)
      rule+=L"        </and>\n";

    rule+=L"        </test>\n";

    if (debug) {
      wstring s=StringUtils::substitute(ats[i].to_wstring(), L"><", L".");
      s=StringUtils::substitute(s,L"<",L"-");
      s=StringUtils::substitute(s,L">",L"");
      rule+=L"        <out>\n";
      rule+=L"          <lu><lit v=\"(rid:"+Utils::itoa(rule_id)+L" at:"+s+L")\"/></lu>\n";
      rule+=L"        </out>\n";
    }
    
    wstring letvarStrs=L"";
    rule+=L"       <out>\n";
    
    if (generate_chunks)
    {
       rule+=L"       <chunk name=\""+chunkName+L"\" case=\"caseFirstWord\">";
       rule+=L"       <tags>";
       rule+=L"             <tag><lit-tag v=\"LRN\"/></tag>";
       rule+=L"       </tags>";
    }
    
    
    int blank_pos=0;
    for(unsigned j=0; j<ats[i].target.size(); j++) {      
      if (ats[i].target[j][0]!='<') { //It's a lexicalized word, we copy it as is
    
    wstring target_tags=Utils::tags2transferformat(Utils::get_tags(ats[i].target[j]));
    wstring tagstoprint=Utils::tags2transferformat(Utils::get_tags(ats[i].target[j]));
	vector<wstring> attributeNames=extract_attribute_names(tagstoprint);
	vector<wstring> tagvector=StringUtils::split_wstring(tagstoprint,L".");
	//remove_generalised_tags(tagstoprint);
	//remove_final_asterisk(tagstoprint);
    
    int pos=-1;
    
    //Some tags come from bilingual dictionary. Get correct gender and number in case of GD/ND
    //if(attributeNames.size() > 0)
//	{
// 		pos=ats[i].get_source_word_pos(j);
// 		rule+=L"        <call-macro n=\"f_set_genre_num\">\n";
// 		rule+=L"          <with-param pos=\""+Utils::itoa(pos+1)+L"\"/>\n";
// 		rule+=L"        </call-macro>\n";
// 	}
    
// 	rule+=L"        <out>\n";
	rule+=L"          <lu>\n";
	rule+=L"            <lit v=\""+StringUtils::substitute(Utils::get_lemma_without_queue(ats[i].target[j]),L"_",L" ")+L"\"/>\n";
	//rule+=L"            <lit-tag v=\""+tagstoprint+L"\"/>\n";
	
	//Some tags come from bilingual dictionary.
	for(vector<wstring>::iterator it=tagvector.begin(); it!=tagvector.end(); ++it){
		if( (*it).substr(0,1)==L"*" )
			rule+=L"            <clip pos=\""+Utils::itoa(pos+1)+L"\" side=\"sl\" part=\"learned_"+(*it).substr(1)+L"\"/>\n";
		else if ( (*it).substr(0,1)==L")" )
		{
			long locpos=Utils::wtol((*it).substr(1,4));
			rule+=L"            <clip pos=\""+Utils::itoa((int) (locpos+1))+L"\" side=\"tl\" part=\"learned_"+(*it).substr(4)+L"\"/>\n";
		}
		else if ( (*it).substr(0,1)==L"(" )
		{
			long locpos=Utils::wtol((*it).substr(1,4));
			rule+=L"            <clip pos=\""+Utils::itoa((int) (locpos+1))+L"\" side=\"sl\" part=\"learned_"+(*it).substr(4)+L"\"/>\n";
		}
		else
			rule+=L"            <lit-tag v=\""+escape_attr((*it))+L"\"/>\n";
		}
	//if(attributeNames.size() > 0)
	//{
	//	for(vector<wstring>::iterator it=attributeNames.begin(); it!=attributeNames.end(); ++it){
	//		rule+=L"            <clip pos=\""+Utils::itoa(pos+1)+L"\" side=\"sl\" part=\""+(*it)+L"\"/>\n";
	//	}
	//}
	//rule+=L"            <lit-tag v=\""+target_tags+L"\"/>\n";
	rule+=L"            <lit v=\""+StringUtils::substitute(Utils::get_queue(ats[i].target[j]),L"_",L" ")+L"\"/>\n";
	rule+=L"          </lu>\n";
// 	rule+=L"        </out>\n";

	//Some tags come from bilingual dictionary. Copy gender/number to global variables
// 	if(attributeNames.size() > 0)
// 	{
// 		rule+=L"        <call-macro n=\"f_genre_num\">\n";
//         rule+=L"          <with-param pos=\""+Utils::itoa(pos+1)+L"\"/>\n";
//         rule+=L"        </call-macro>\n";
// 	}
	
	//Copy gender/number to global variables in case that they come directly from AT
	wstring genre=Utils::get_tag_value(tagstoprint,L"m|f");
	if(genre.length()>0)
	  letvarStrs+=L"        <let><var n=\"genre\"/><lit-tag v=\""+genre+L"\"/></let>\n";
	wstring number=Utils::get_tag_value(tagstoprint,L"sg|pl");
	if(number.length()>0)
	  letvarStrs+=L"        <let><var n=\"number\"/><lit-tag v=\""+number+L"\"/></let>\n";

      } else {

	wstring tagstoprint=Utils::tags2transferformat(Utils::get_tags(ats[i].target[j]));
	vector<wstring> attributeNames=extract_attribute_names(tagstoprint);
	vector<wstring> tagvector=StringUtils::split_wstring(tagstoprint,L".");
	
	//remove_generalised_tags(tagstoprint);
	//remove_final_asterisk(tagstoprint);
	int pos=ats[i].get_first_open_source_word_pos(j);
	
	//Some tags come from bilingual dictionary. Get correct gender and number in case of GD/ND
//     if(attributeNames.size() > 0)
// 	{
// 		int pos=ats[i].get_source_word_pos(j);
// 		rule+=L"        <call-macro n=\"f_set_genre_num\">\n";
// 		rule+=L"          <with-param pos=\""+Utils::itoa(pos+1)+L"\"/>\n";
// 		rule+=L"        </call-macro>\n";
// 	}
	
// 	rule+=L"        <out>\n";
	rule+=L"          <lu>\n";
	rule+=L"            <clip pos=\""+Utils::itoa(pos+1)+L"\" side=\"tl\" part=\"lemh\"/>\n";
	
	
	for(vector<wstring>::iterator it=tagvector.begin(); it!=tagvector.end(); ++it){
		if( (*it).substr(0,1)==L"*" )
			rule+=L"            <clip pos=\""+Utils::itoa(pos+1)+L"\" side=\"sl\" part=\"learned_"+(*it).substr(1)+L"\"/>\n";
		else if ( (*it).substr(0,1)==L")" )
		{
			long locpos=Utils::wtol((*it).substr(1,4));
			rule+=L"            <clip pos=\""+Utils::itoa((int) (locpos+1))+L"\" side=\"tl\" part=\"learned_"+(*it).substr(4)+L"\"/>\n";
		}
		else if ( (*it).substr(0,1)==L"(" )
		{
			long locpos=Utils::wtol((*it).substr(1,4));
			rule+=L"            <clip pos=\""+Utils::itoa((int) (locpos+1))+L"\" side=\"sl\" part=\"learned_"+(*it).substr(4)+L"\"/>\n";
		}
		else
			rule+=L"            <lit-tag v=\""+escape_attr((*it))+L"\"/>\n";
	}
	
	//rule+=L"            <lit-tag v=\""+tagstoprint+L"\"/>\n";
	
	//for(vector<wstring>::iterator it=attributeNames.begin(); it!=attributeNames.end(); ++it){
	//	rule+=L"            <clip pos=\""+Utils::itoa(pos+1)+L"\" side=\"tl\" part=\""+(*it)+L"\"/>\n";
	//}
	
	rule+=L"            <clip pos=\""+Utils::itoa(pos+1)+L"\" side=\"tl\" part=\"lemq\"/>\n";
	rule+=L"          </lu>\n";
// 	rule+=L"        </out>\n";

        
        //Some tags come from bilingual dictionary. Copy gender/number to global variables
// 	if(attributeNames.size() > 0)
// 	{
//         rule+=L"        <call-macro n=\"f_genre_num\">\n";
//         rule+=L"          <with-param pos=\""+Utils::itoa(pos+1)+L"\"/>\n";
//         rule+=L"        </call-macro>\n";
//      }
        
	//Copy gender/number to global variables in case that they come directly from AT
	wstring genre=Utils::get_tag_value(tagstoprint,L"m|f");
	if(genre.length()>0)
	  letvarStrs+=L"        <let><var n=\"genre\"/><lit-tag v=\""+genre+L"\"/></let>\n";
	wstring number=Utils::get_tag_value(tagstoprint,L"sg|pl");
	if(number.length()>0)
	  letvarStrs+=L"        <let><var n=\"number\"/><lit-tag v=\""+number+L"\"/></let>\n";
        
      }

      if (blank_pos<(int)(ats[i].source.size()-1)) {
// 	rule+=L"        <out>\n";
	rule+=L"          <b pos=\""+Utils::itoa(blank_pos+1)+L"\"/>\n";
// 	rule+=L"        </out>\n";
	blank_pos++;
      } else if (j<(ats[i].target.size()-1)) {
	//TL output string has more words than the SL pattern detected
// 	rule+=L"        <out>\n";
	rule+=L"          <b/>\n";
// 	rule+=L"        </out>\n";
      }
    }

     if (generate_chunks)
     {
       rule+=L"      </chunk>\n";
     }
    rule+=L"      </out>\n";
    
     if (debug) {
      rule+=L"        <out>\n";
      rule+=L"          <lu><lit v=\"(END)\"/></lu>\n";
      rule+=L"        </out>\n";
    }
    
    //If there are remaining blanks we print them out if they have
    //format information inside. This is caused by a SL input string
    //longer than the TL output one
    for (unsigned j=ats[i].target.size(); j<ats[i].source.size(); j++) {
      rule+=L"        <call-macro n=\"f_bcond\">\n";
      rule+=L"          <with-param pos=\""+Utils::itoa(j)+L"\"/>\n";
      rule+=L"          <with-param pos=\""+Utils::itoa(j+1)+L"\"/>\n";
      rule+=L"        </call-macro>\n";
    }
    
    rule+=letvarStrs;
    rule+=L"      </when>\n";

    if(!include_otherwise) {
      //As the condition will always be met it has no sense to include
      //further ATs
      break;
    }
  }



  //Actions to perform when none of the ATs can be applied
  //word-for-word translation
  if(include_otherwise) {
    rule+=L"      <otherwise><!--Word-for-word translation-->\n";
     if (debug) {
      rule+=L"        <out>\n";
      rule+=L"          <lu><lit v=\"(rid:"+Utils::itoa(rule_id)+L" at:word-for-word)\"/></lu>\n";
      rule+=L"        </out>\n";
    }
    
	  if(use_discard_rule)
	  {
		rule+=L"        <reject-current-rule shifting=\"no\" />\n";
	  }
	  else
	  {

    for(unsigned i=0; i<ats[0].source.size(); i++) {
      rule+=L"        <call-macro n=\"f_genre_num\">\n";
      rule+=L"          <with-param pos=\""+Utils::itoa(i+1)+L"\"/>\n";
      rule+=L"        </call-macro>\n";

      rule+=L"        <call-macro n=\"f_set_genre_num\">\n";
      rule+=L"          <with-param pos=\""+Utils::itoa(i+1)+L"\"/>\n";
      rule+=L"        </call-macro>\n";

      rule+=L"        <out>\n";
      rule+=L"          <lu>\n";

      rule+=L"            <clip pos=\""+Utils::itoa(i+1)+L"\" side=\"tl\" part=\"whole\"/>\n";
      //rule+=L"            <clip pos=\""+Utils::itoa(i+1)+L"\" side=\"tl\" part=\"lemh\"/>\n";
      //rule+=L"            <clip pos=\""+Utils::itoa(i+1)+L"\" side=\"tl\" part=\"tags\"/>\n";
      //rule+=L"            <clip pos=\""+Utils::itoa(i+1)+L"\" side=\"tl\" part=\"lemq\"/>\n";

      rule+=L"          </lu>\n";
      if (i<(ats[0].source.size()-1))
	rule+=L"          <b pos=\""+Utils::itoa(i+1)+L"\"/>\n";
      rule+=L"        </out>\n";
    }
    if (debug) {
      rule+=L"        <out>\n";
      rule+=L"          <lu><lit v=\"(END)\"/></lu>\n";
      rule+=L"        </out>\n";
    }
  }

    rule+=L"      </otherwise>\n";
  }

  rule+=L"    </choose>\n";
  rule+=L"  </action>\n";
  rule+=L"</rule>\n";

  return rule;
}

wstring 
TransferRule::gen_apertium_transfer_head(bool debug) {

  locale loc(setlocale(LC_ALL,""));
  wstring head=L"";

  head+=L"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
  head+=L"<!-- -*- nxml -*- -->\n";
  head+=L"<transfer>\n";

  head+=L"<section-def-cats>\n";

  set<pair<wstring,wstring> >::iterator it;
  for(it=categories.begin(); it!=categories.end(); it++) {
    head+=L"  <def-cat n=\"CAT__"+category_name(it->first,it->second)+L"\">\n";
    if (it->first.length()>0) //There is a lemma
    {
      head+=L"    <cat-item lemma=\""+StringUtils::substitute(it->first,L"_",L" ")+L"\" tags=\""+escape_attr(it->second)+L"\"/>\n";
      
      //Lemma in upper case too
      head+=L"    <cat-item lemma=\"";
      head+=toupper<wchar_t>(StringUtils::substitute(it->first,L"_",L" ")[0],loc);
      head+=StringUtils::substitute(it->first,L"_",L" ").substr(1)+L"\" tags=\""+escape_attr(it->second)+L"\"/>\n";
    }
    else
    {
      head+=L"    <cat-item tags=\""+escape_attr(it->second)+L"\"/>\n";
      if(sm_generalise ||  it->second[it->second.size()-1]==L'*'  )
	head+=L"    <cat-item tags=\""+escape_attr((it->second).substr(0,it->second.size()-2))+L"\"/>\n";
    }
    head+=L"  </def-cat>\n";
  }

  head+=L"<def-cat n=\"CAT__HASGENDER_NUMBER\"><cat-item tags=\"*.m.*\"/><cat-item tags=\"*.f.*\"/><cat-item tags=\"*.sg.*\"/><cat-item tags=\"*.pl.*\"/></def-cat>";

  head+=L"  <def-cat n=\"CAT__ND_GD\">\n";
  head+=L"    <cat-item tags=\"*.mf.*\"/>\n";
  head+=L"    <cat-item tags=\"*.sp.*\"/>\n";
  head+=L"    <cat-item tags=\"*.mf.sp.*\"/>\n";
  head+=L"    <cat-item tags=\"*.sp.mf.*\"/>\n";
  head+=L"    <cat-item tags=\"*.mf.*.sp.*\"/>\n";
  head+=L"    <cat-item tags=\"*.sp.*.mf.*\"/>\n";
  head+=L"  </def-cat>\n";
  
  head+=L"  <def-cat n=\"sent\">\n";
  head+=L"    <cat-item tags=\"sent\"/>\n";
  head+=L"    <cat-item tags=\"RESsent.sent\"/>\n";
  head+=L"  </def-cat>\n";
  
  head+=L"  <def-cat n=\"any\">\n";
  head+=L"    <cat-item tags=\"*\"/>\n";
  head+=L"  </def-cat>\n";

  head+=L"</section-def-cats>\n";

  head+=L"<section-def-attrs>\n";

  //set<string>::iterator it2;
  //for(it2=attributes.begin(); it2!=attributes.end(); it2++) {
  //  head+="  <def-attr n=\"ATTR__"+category_name("",(*it2))+"\">\n";
  //  head+="    <attr-item tags=\""+(*it2)+"\"/>\n";
  //  head+="  </def-attr>\n";
  //}
  
  
  map<wstring,pair< set<wstring>, set<wstring> > >::iterator it2;
  for(it2=attributes.begin(); it2!=attributes.end(); it2++) {
    head+=L"  <def-attr n=\"learned_"+(*it2).first+L"\">\n";
    set<wstring> tagsfromattr=(*it2).second.first;
    for(set<wstring>::iterator it3= tagsfromattr.begin(); it3!=tagsfromattr.end(); ++it3)
		head+=L"    <attr-item tags=\""+StringUtils::substitute((*it3),L"+",L"\\+")+L"\"/>\n";
    head+=L"  </def-attr>\n";
  }

  head+=L"  <def-attr n=\"learned_gen\">\n";
  head+=L"    <attr-item tags=\"m\"/>\n";
  head+=L"    <attr-item tags=\"f\"/>\n";
  head+=L"    <attr-item tags=\"mf\"/>\n";
  head+=L"    <attr-item tags=\"GD\"/>\n";
  head+=L"  </def-attr>\n";

  head+=L"  <def-attr n=\"learned_num\">\n";
  head+=L"    <attr-item tags=\"sg\"/>\n";
  head+=L"    <attr-item tags=\"pl\"/>\n";
  head+=L"    <attr-item tags=\"sp\"/>\n";
  head+=L"    <attr-item tags=\"ND\"/>\n";
  head+=L"  </def-attr>\n";

  //head+="  <def-attr n=\"ATTR__notused\">\n";
  //head+="    <attr-item tags=\"this.attr.will.not.be.used\"/>\n";
  //head+="  </def-attr>\n";

  head+=L"</section-def-attrs>\n";

  head+=L"<section-def-vars>\n";
  head+=L"  <def-var n=\"genre\"/>\n";
  head+=L"  <def-var n=\"number\"/>\n";
  head+=L"</section-def-vars>\n";

  head+=L"<section-def-macros>\n";

  head+=L"<def-macro n=\"f_bcond\" npar=\"2\">\n";
  head+=L"<!--To test whether a blank contains format information.\n";
  head+=L"If no format information is present it is removed. -->\n";
  head+=L"  <choose>\n";
  head+=L"    <when>\n";
  head+=L"      <test>\n";
  head+=L"        <not>\n";
  head+=L"	 <equal>\n";
  head+=L"	   <b pos=\"1\"/>\n";
  head+=L"	   <lit v=\" \"/>\n";
  head+=L"	 </equal>\n";
  head+=L"	 </not>\n";
  head+=L"      </test>\n";
  head+=L"      <out>\n";
  head+=L"        <b pos=\"1\"/>\n";
  head+=L"      </out>\n";
  head+=L"    </when>\n";
  head+=L"  </choose>\n";
  head+=L"</def-macro>\n";

  head+=L"<def-macro n=\"f_genre_num\" npar=\"1\">\n";
  head+=L"<!--To set the global value storing the TL genre of the last seen word. -->\n";
  head+=L"  <choose>\n";
  head+=L"    <when>\n";
  head+=L"      <test>\n";
  head+=L"        <equal>\n";
  head+=L"          <clip pos=\"1\" side=\"tl\" part=\"learned_gen\"/>\n";
  head+=L"          <lit-tag v=\"m\"/>\n";
  head+=L"        </equal>\n";
  head+=L"      </test>\n";
  head+=L"      <let><var n=\"genre\"/><lit-tag v=\"m\"/></let>\n";
  head+=L"    </when>\n";
  head+=L"    <when>\n";
  head+=L"      <test>\n";
  head+=L"        <equal>\n";
  head+=L"          <clip pos=\"1\" side=\"tl\" part=\"learned_gen\"/>\n";
  head+=L"          <lit-tag v=\"f\"/>\n";
  head+=L"        </equal>\n";
  head+=L"      </test>\n";
  head+=L"      <let><var n=\"genre\"/><lit-tag v=\"f\"/></let>\n";
  head+=L"    </when>\n";
  head+=L"  </choose>\n";
  head+=L"  <choose>\n";
  head+=L"    <when>\n";
  head+=L"      <test>\n";
  head+=L"        <equal>\n";
  head+=L"          <clip pos=\"1\" side=\"tl\" part=\"learned_num\"/>\n";
  head+=L"          <lit-tag v=\"sg\"/>\n";
  head+=L"        </equal>\n";
  head+=L"      </test>\n";
  head+=L"      <let><var n=\"number\"/><lit-tag v=\"sg\"/></let>\n";
  head+=L"    </when>\n";
  head+=L"    <when>\n";
  head+=L"      <test>\n";
  head+=L"        <equal>\n";
  head+=L"          <clip pos=\"1\" side=\"tl\" part=\"learned_num\"/>\n";
  head+=L"          <lit-tag v=\"pl\"/>\n";
  head+=L"        </equal>\n";
  head+=L"      </test>\n";
  head+=L"      <let><var n=\"number\"/><lit-tag v=\"pl\"/></let>\n";
  head+=L"    </when>\n";
  head+=L"  </choose>\n";
  head+=L"</def-macro>\n";

 
  head+=L"<def-macro n=\"f_set_genre_num\" npar=\"1\">\n";
  head+=L"<!--To set the genre of those words with GD, and the number of those words with ND. -->\n";
  head+=L"<!--This is only used in no alignment template at all is applied. -->\n";
  
  if(no_vars_determined)
  {
	   head+=L"  <choose>\n";
	  head+=L"    <when>\n";
	  head+=L"      <test>\n";
	  head+=L"        <equal>\n";
	  head+=L"          <clip pos=\"1\" side=\"tl\" part=\"learned_gen\"/>\n";
	  head+=L"          <lit-tag v=\"GD\"/>\n";
	  head+=L"        </equal>\n";
	  head+=L"      </test>\n";
	  //head+=L"      <let><clip pos=\"1\" side=\"tl\" part=\"gen\"/><lit-tag v=\"m\"/></let>\n";
	  head+=L"    </when>\n";
	  head+=L"  </choose>\n";
	  head+=L"  <choose>\n";
	  head+=L"    <when>\n";
	  head+=L"      <test>\n";
	  head+=L"        <equal>\n";
	  head+=L"          <clip pos=\"1\" side=\"tl\" part=\"learned_num\"/>\n";
	  head+=L"          <lit-tag v=\"ND\"/>\n";
	  head+=L"        </equal>\n";
	  head+=L"      </test>\n";
	  //head+=L"      <let><clip pos=\"1\" side=\"tl\" part=\"num\"/><lit-tag v=\"sg\"/></let>\n";
	  head+=L"    </when>\n";
	  head+=L"  </choose>\n";
  }
  else
  {
	  head+=L"  <choose>\n";
	  head+=L"    <when>\n";
	  head+=L"      <test>\n";
	  head+=L"        <equal>\n";
	  head+=L"          <clip pos=\"1\" side=\"tl\" part=\"learned_gen\"/>\n";
	  head+=L"          <lit-tag v=\"GD\"/>\n";
	  head+=L"        </equal>\n";
	  head+=L"      </test>\n";
	  head+=L"      <choose>\n";
	  head+=L"        <when>\n";
	  head+=L"          <test>\n";
	  head+=L"            <equal>\n";
	  head+=L"              <var n=\"genre\"/>\n";
	  head+=L"              <lit-tag v=\"f\"/>\n";
	  head+=L"            </equal>\n";
	  head+=L"          </test>\n";
	  head+=L"          <let><clip pos=\"1\" side=\"tl\" part=\"learned_gen\"/><lit-tag v=\"f\"/></let>\n";
	  head+=L"        </when>\n";
	  head+=L"        <otherwise>\n";
	  head+=L"          <let><clip pos=\"1\" side=\"tl\" part=\"learned_gen\"/><lit-tag v=\"m\"/></let>\n";
	  head+=L"        </otherwise>\n";
	  head+=L"      </choose>\n";
	  head+=L"    </when>\n";
	  head+=L"  </choose>\n";
	  head+=L"  <choose>\n";
	  head+=L"    <when>\n";
	  head+=L"      <test>\n";
	  head+=L"        <equal>\n";
	  head+=L"          <clip pos=\"1\" side=\"tl\" part=\"learned_num\"/>\n";
	  head+=L"          <lit-tag v=\"ND\"/>\n";
	  head+=L"        </equal>\n";
	  head+=L"      </test>\n";
	  head+=L"      <choose>\n";
	  head+=L"        <when>\n";
	  head+=L"          <test>\n";
	  head+=L"            <equal>\n";
	  head+=L"              <var n=\"number\"/>\n";
	  head+=L"              <lit-tag v=\"pl\"/>\n";
	  head+=L"            </equal>\n";
	  head+=L"          </test>\n";
	  head+=L"          <let><clip pos=\"1\" side=\"tl\" part=\"learned_num\"/><lit-tag v=\"pl\"/></let>\n";
	  head+=L"        </when>\n";
	  head+=L"        <otherwise>\n";
	  head+=L"          <let><clip pos=\"1\" side=\"tl\" part=\"learned_num\"/><lit-tag v=\"sg\"/></let>\n";
	  head+=L"        </otherwise>\n";
	  head+=L"      </choose>\n";
	  head+=L"    </when>\n";
	  head+=L"  </choose>\n";
  }
  
  
  head+=L"</def-macro>\n";

  head+=L"</section-def-macros>\n";

  head+=L"<section-rules>\n";

  return head;
}

wstring 
TransferRule::gen_apertium_transfer_foot(bool debug) {
  wstring foot=L"";

  foot+=L"<rule>\n";
  foot+=L"  <pattern>\n";
  foot+=L"    <pattern-item n=\"CAT__ND_GD\"/>\n";
  foot+=L"  </pattern>\n";
  foot+=L"  <action>\n";

  if(debug) {
    foot+=L"  <out>\n";
    foot+=L"    <lu><lit v=\"(default)\"/></lu>\n";
    foot+=L"  </out>\n";
  }

  foot+=L"  <call-macro n=\"f_set_genre_num\">\n";
  foot+=L"    <with-param pos=\"1\"/>\n";
  foot+=L"  </call-macro>\n";
  foot+=L"  <out>\n";
  foot+=L"    <lu>\n";
  foot+=L"      <clip pos=\"1\" side=\"tl\" part=\"whole\"/>\n";
  foot+=L"    </lu>\n";
  foot+=L"  </out>\n";
  foot+=L"  </action><!--isolated word-->\n";
  foot+=L"</rule>\n";
  
  foot+=L"<rule>\n";
  foot+=L"<pattern><pattern-item n=\"CAT__HASGENDER_NUMBER\"/></pattern><action> <call-macro n=\"f_genre_num\"><with-param pos=\"1\"/></call-macro> <call-macro n=\"f_set_genre_num\"><with-param pos=\"1\"/></call-macro> <out><lu> <clip pos=\"1\" side=\"tl\" part=\"whole\"/></lu></out> </action><!--isolated word-->\n";
  foot+=L"</rule>\n";
  
  foot+=L"<rule>\n";
  foot+=L"<pattern><pattern-item n=\"sent\"/></pattern><action> <let><var n=\"number\"/> <lit-tag v=\"sg\"/></let><let><var n=\"genre\"/><lit-tag v=\"m\"/></let> <out><lu> <clip pos=\"1\" side=\"tl\" part=\"whole\"/></lu></out></action><!--isolated word-->\n";
  foot+=L"</rule>\n";
  
  foot+=L"<rule>\n";
  foot+=L"<pattern><pattern-item n=\"any\"/></pattern><action>  <out><lu> <clip pos=\"1\" side=\"tl\" part=\"whole\"/></lu></out> </action><!--isolated word-->\n";
  foot+=L"</rule>\n";
  
  foot+=L"</section-rules>\n";
  foot+=L"</transfer>\n";

  return foot;
}

wstring 
TransferRule::category_name(const wstring& lemma, const wstring& tags) {
  wstring catname=L"";

  if (lemma.length()>0)//TODO: codificar bien el caracter extraño
    catname+=StringUtils::substitute(StringUtils::substitute(StringUtils::substitute(lemma,L"#",L"_"),L"\u2019",L"_"),L"'",L"QUOT")+L"_";

  catname+=StringUtils::substitute(StringUtils::substitute(StringUtils::substitute(StringUtils::substitute(tags,L".",L""),L"*",L"_"),L"+",L"plus"),L"@",L"arroba");

  return catname;
}

 wstring 
 TransferRule::escape_attr(const wstring attrstr){
  return  StringUtils::substitute(attrstr,L"+",L"\\+");
 }

wstring 
TransferRule::attribute_pos_group_name(const wstring& pos)
{
	wstring attrname=L"ispartofspeech"+pos;
	
	return attrname;
}



int
TransferRule::load_attributes(istream* fin) {
	string oneline;
	wstring wline;
	while (!fin->eof()) {
		getline(*fin,oneline);
		wline=UtfConverter::fromUtf8(oneline);
		vector<wstring> parts=StringUtils::split_wstring(wline,L":");
		if (parts.size()>=2){
			vector<wstring> tags=StringUtils::split_wstring(parts[1],L",");
			set<wstring> tagset(tags.begin(),tags.end());
			pair< set<wstring>,set<wstring> > content;
			content.first=tagset;
			//content.second=L"";
			if (parts.size() >= 3)
			{
			   vector<wstring> postags=StringUtils::split_wstring(parts[2],L",");
			   set<wstring> postagsset(postags.begin(),postags.end());
			   content.second=postagsset;
			}
			attributes[parts[0]]=content;
		}
	}
}

wstring
TransferRule::get_attribute_for_tag(wstring &tag, wstring &pos) {
	wstring attrname=L"";
	if(tag.size() >= 10 && tag.substr(0,10)==L"empty_tag_")
		attrname=L"learned_"+tag.substr(10);
	else
	{
		for ( map<wstring, pair< set<wstring>, set<wstring> > >::iterator  it=  attributes.begin() ; it != attributes.end(); it++ ){
			//wcerr<<L"looking for '"+tag+L"' in '"+(*it).first+L"'"<<endl;
			if ((*it).second.first.find(tag)!=(*it).second.first.end() && ((*it).second.second.size() ==0 || (*it).second.second.find(pos) != (*it).second.second.end() ) )
				attrname=L"learned_"+(*it).first;
		}
	}
	return attrname;
}

void
TransferRule::remove_generalised_tags(wstring &tags)
{
	wchar_t c;
    for(int i=0; i<tags.size(); i++)
    {
		c=tags[i];
		if(c == L'*')
		{
			tags=tags.substr(0,i+1);
			break;
		}
	} 
}

void
TransferRule::remove_final_asterisk(wstring &tags)
{
	wchar_t c;
	if(tags.size() >= 2)
	{
			if(tags[tags.size()-1]==L'*' && tags[tags.size()-2]==L'.')
				tags=tags.substr(0,tags.size()-2);
	}
}

vector<wstring>
TransferRule::extract_attribute_names(wstring &tags)
{
	vector<wstring> output;
	vector<wstring> pieces=StringUtils::split_wstring(tags,L".");
	for(int i=0; i< pieces.size(); i++){
		if (pieces[i][0]==L'*')
			output.push_back(L"learned_"+pieces[i].substr(1));
	}
	return output;	
}
