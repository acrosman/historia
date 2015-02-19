#!/usr/local/bin/python3
# encoding: utf-8
"""
user_db.py

Created by Aaron Crosman on 2015-02-18.

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

from Crypto.Cipher import AES
from Crypto import Random

from .core_data_objects import *
from .settings import *
from .exceptions import *


class HistoriaUserDatabase(HistoriaDatabase, HistoriaDataObject):
    type_label = "Historia User Database"
    machine_type = "historia_user_database"
    
    _table_fields      = {'id': {
                                'type':       'int',
                                'length':     '11',
                                'signed':     False,
                                'allow_null': False,
                                'default':    'AUTO_INCREMENT',
                                'index':      { 'type':'PRIMARY', 'fields': ('id',)},
                                'order': 0
                                },
                            'db_name': {
                                'type':       'varchar',
                                'length': '255',
                                'allow_null': False,
                                'index':      { 'type':'UNIQUE', 'fields': ('db_name',)},
                                'order': 1
                            },
                            'uid': {
                                'type':       'int',
                                'length':     '11',
                                'allow_null': False,
                                'index':      { 'type':'BASIC', 'fields': ('uid',)},
                                'order': 2
                            },
                            'db_password': {
                                'type': 'longblob',
                                'allow_null': False,
                                'order': 3
                            },
                            'password_aed_iv': {
                                'type': 'blob',
                                'allow_null':False,
                                'order',4
                            },
                            'db_user': {
                                'type': 'varchar',
                                'length': '255',
                                'allow_null': False,
                                'order': 5
                            },
                            'db_address': {
                                'type': 'char',
                                'length': '128',
                                'allow_null': False,
                                'order': 6
                            },
                            'last_record_update':{
                                'type':'timestamp',
                                'allow_null': False,
                                'update_timestamp': True,
                                'default': 'CURRENT_TIMESTAMP',
                                'order': 7
                            },
                            'created':{
                                'type':'datetime',
                                'allow_null': False,
                                'default': None,
                                'order': 8
                            },    
                            'last_login':{
                                'type':'datetime',
                                'allow_null': False,
                                'default': None,
                                'order': 9
                            },
                            'enabled':{
                                'type':'tinyint',
                                'length': 1,
                                'allow_null': False,
                                'default':'1',
                                'order': 10
                            }
                        }
    
    
    def __init__(self, database_name):
        super().__init__(database_name)
        
        self.member_classes = [
        
        ]
        
    def __setattr__(self, name, value):
        """
        Use __setattr__ to detect changes to the object so that we can check
        the field list for value attributes and to set the dirty bit to see
        if a save is required. 
        For a userdb, this also handle password encryption.
        """

        # Ban @ from the name column to avoid email addresses appearing there.
        try:
            if name == 'name' and "@" in value:
                raise ValueError("@ not permitted in user name.")
        except TypeError as err:
            pass

        # Create a bypass so we can load vaules from the database without trouble.
        if name == 'password' and value is not None:
            value = self._decrypt_password(value)

        # Since all the general checking is at in HistoriaRecord, do the checking there.
        HistoriaRecord.__setattr__(self, name, value)

    def _encrypt_password(self, value):
        key = b'Sixteen byte key' # <-- needs to be loaded from a file set in config
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CFB, iv)
        msg = iv + cipher.encrypt(value)
        return msg
        
    def _decrypt_password(self, secure_text, iv):
        key = b'Sixteen byte key' # <-- needs to be loaded from a file set in config
        cipher = AES.new(key, AES.MODE_CFB, iv)
        password =  cipher.decrypt(secure_text)
        return password
        

if __name__ == '__main__':
    import unittest
    
    import tests.test_user_db
    
    localtests = unittest.TestLoader().loadTestsFromModule(tests.test_user_db)
    unittest.TextTestRunner(verbosity=2).run(localtests)
