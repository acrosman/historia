#!/usr/bin/env python3
# encoding: utf-8
"""
settings.py

Created by Aaron Crosman on 2015-01-28.

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

import sys
import os

from .core_data_objects import *
from .exceptions import *


class HistoriaSetting(HistoriaRecord):
    
    type_label        = "Historia Settings Record"
    machine_type      = "historia_settings"
    _table_fields     = {'name': {
                                'type':       'varchar',
                                'default':  None,
                                'length':     '255',
                                'allow_null': False,
                                'index':      { 'type':'PRIMARY', 'fields': ('name',)},
                                'order': 0
                            },
                        'value': {
                                'type':       'longblob',
                                'default': '',
                                'allow_null': False,
                                'order': 1
                            }
                        }
    # The table fields here are just present for testing and are not expected to be used
    # Fields are defined as follows (this should get documented someplace better)
    # _table_fields = {'field_name': {'type': [type_name], 
    #                                'length': [as_needed_by_type], 
    #                                'signed': [TRUE/FALSE]
    #                                'allow_null': [TRUE/FALSE],
    #                                'default': [default value or NULL or AUTO_INCREMENT],
    #                                'update_timestamp': [TRUE/FALSE on timestamp field only],
    #                                'index' : {'type' : [PRIMARY/UNIQUE/BASIC], 
    #                                           'name' : [Optional name],
    #                                           'fields': [List, of, fields]}
    #                }}
    
    
    def __eq__(self, other):
        if self.name == None:
            return False
        else:
            try:
                if self.machine_type == other.machine_type:
                    return self.name == other.name and self.value == other.value
                else:
                    return False
            except AttritbuteError:
                return False

    def __ne__(self, other):
        if self.name == None:
            return True
        else:
            try: 
                if self.machine_type == other.machine_type:
                    return self.name != other.name or self.value != other.value
                else:
                    return True
            except AttritbuteError:
                return True
    
    def save(self):
        """Save this record to the database."""

        if self.id == -1:
            self._id = self.database.execute_insert(self._generate_insert_SQL())
        else:
            self.database.execute_update(self._generate_update_SQL())
        
        self._dirty = False

    def load(self, recordID):
        """Load a record from the database into this object."""

        if self.id != -1:
            raise DataLoadError("Cannot load a record into a record object already in new.  Memory is cheap, create a new one.")

        data = self.database.execute_select(self._generate_select_SQL(recordID))[0]

        for field in data:
            setattr(self, field, data[field])
        
        self.value = self.value.decode('utf-8') # decode the blob...let's not use a lot of these.
        
        self._dirty = False

    

if __name__ == '__main__':
    import unittest

    import tests.test_settings

    localtests = unittest.TestLoader().loadTestsFromModule(tests.test_settings_obj)
    unittest.TextTestRunner(verbosity=2).run(localtests)
