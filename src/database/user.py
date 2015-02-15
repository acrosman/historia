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

import bcrypt

from .core_data_objects import *
from .exceptions import *


class HistoriaUser(HistoriaRecord):
    
    type_label        = "Historia User"
    machine_type      = "historia_user"
    _table_fields      = {'id': {
                                'type':       'int',
                                'length':     '11',
                                'signed':     False,
                                'allow_null': False,
                                'default':    'AUTO_INCREMENT',
                                'index':      { 'type':'PRIMARY', 'fields': ('id',)},
                                'order': 0
                                },
                            'name': {
                                'type':       'varchar',
                                'length': '255',
                                'allow_null': False,
                                'index':      { 'type':'UNIQUE', 'fields': ('name',)},
                                'order': 1
                            },
                            'email': {
                                'type':       'varchar',
                                'length': '255',
                                'allow_null': False,
                                'index':      { 'type':'UNIQUE', 'fields': ('email',)},
                                'order': 2
                            },
                            'password': {
                                'type': 'char',
                                'length': '60',
                                'allow_null': False,
                                'order': 3
                            },
                            'modified':{
                                'type':'timestamp',
                                'allow_null': False,
                                'update_timestamp': True,
                                'default': 'CURRENT_TIMESTAMP',
                                'order': 4
                            },
                            'created':{
                                'type':'datetime',
                                'allow_null': False,
                                'default': None,
                                'order': 5
                            },
                            'last_access':{
                                'type':'datetime',
                                'allow_null': True,
                                'default': None,
                                'order': 6
                            },
                            'enabled':{
                                'type':'tinyint',
                                'length': 1,
                                'allow_null': False,
                                'default':'1',
                                'order': 7
                            },
                            'admin':{
                                'type':'tinyint',
                                'length': 1,
                                'allow_null': False,
                                'default':'0',
                                'order': 9
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
    
    
    def __setattr__(self, name, value):
        """
        Use __setattr__ to detect changes to the object so that we can check
        the field list for value attributes and to set the dirty bit to see
        if a save is required. 
        For a user, this also handle password encryption.
        """
        
        if name == 'password' and value is not None:
            if not isinstance(value, str):
                raise ValueError("Password must be strings.")
            value = bcrypt.hashpw(value, bcrypt.gensalt())
        
        # Ban @ from the name column to avoid email addresses appearing there.
        try:
            if name == 'name' and "@" in value:
                raise ValueError("@ not permitted in user name.")
        except TypeError as err:
            pass
        
        # Create a bypass so we can load vaules from the database without trouble.
        if name == '_password' and value is not None:
            name = 'password'
        
        # Since all the general checking is at in HistoriaRecord, do the checking there.
        HistoriaRecord.__setattr__(self, name, value)
        
                
    def checkPassword(self, testPassword):
        """checkPassword: use bcrypt to test of testPassword matches the password on file."""
        return bcrypt.hashpw(testPassword, self.password) == self.password
    
    def load(self, recordID):
        """Load a user from the database into this object, don't double encrypt the password."""

        if self.id != -1:
            raise DataLoadError("Cannot load a record into a record object already in new.  Memory is cheap, create a new one.")

        data = self.database.execute_select(self._generate_select_SQL(recordID))[0]
        
        for field in data:
            if field == 'id':
                self._id = data[field]
            elif field == 'password':
                self._password = data[field]
            else:
                setattr(self, field, data[field])

        self._dirty = False

if __name__ == '__main__':
    import unittest

    import tests.test_settings

    localtests = unittest.TestLoader().loadTestsFromModule(tests.test_settings_obj)
    unittest.TextTestRunner(verbosity=2).run(localtests)
