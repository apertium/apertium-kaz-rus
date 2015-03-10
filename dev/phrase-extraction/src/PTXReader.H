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

#ifndef __PTXREADER_
#define __PTXREADER_

#include <libxml/xmlreader.h>
#include <string>
#include <vector>
#include <iostream>

using namespace std;

class PTXReader {
private:
  xmlTextReaderPtr reader;  

  vector<vector<wstring> > mlu; //multilexical units, a vector of
			       //lexical units

  wstring name;
  int type;

  void copy(PTXReader const &o);

  void destroy();

  void step();

  wstring attrib(wstring const &name);

  void parseError(wstring const &message);

  void proc_mlu();
  void proc_lu(vector<wstring>& one_mlu);

public:

  PTXReader();

  ~PTXReader();

  PTXReader(PTXReader const &o);

  PTXReader & operator =(PTXReader const &o);

  void read(string const &filename);

  vector<vector<wstring> > get_all_mlu();
};

#endif
