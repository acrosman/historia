#!/usr/local/bin/python3
# encoding: utf-8
"""
historia_json_encoder.py.py

This file is part of the internals package. It provides a simple class to that
implements a JSONEncoder to ensure Historia Objects can easily be encoded 
correctly, even when they are in lists and other similar structures.


Created by Aaron Crosman on 2015-06-07

    This file is part of historia.

    historia is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    historia is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with historia.  If not, see <http://www.gnu.org/licenses/>.

"""

import json

class HistoriaJSONEncoder(json.JSONEncoder):
     def default(self, obj):
         try:
             return obj.to_dict()
         except AttributeError as err:
             return json.JSONEncoder.default(self, obj)
