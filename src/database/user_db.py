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


class HistoriaUserDatabase(HistoriaDatabase, HistoriaRecord):
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
                        'password_aes_iv': {
                            'type': 'blob',
                            'allow_null':False,
                            'order':4
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
    
    
    def __init__(self, master_database, database_name, key_file):
        HistoriaDatabase.__init__(self,database_name)
        
        try:
            with open (key_file, 'rb') as key_data:
                self._aes_key = key_data.read()
        except Exception as err:
            self._logger.error("Unable to load key data from {0}".format(key_file))
            raise
            
        # Assign all the attributes for the class list of fields
        for field in type(self)._table_fields:
            if field is not 'id':
                setattr(self, field, None)
            else:
                self._id = -1
        
        self.db_password = ''
        self.database = master_database
        
        self.member_classes = [
        
        ]
        
    
    def __setattr__(self, name, value):
        """Override the __setattr__ provided by HistoriaRecord to allow a special case for member_classes."""
        
        valid_db_names = ['member_classes', 'connection_settings', 'name', 'database_defaults', 'connection', 'database']
        
        if name in valid_db_names:
            HistoriaDatabase.__setattr__(self, name, value)
        else:
            HistoriaRecord.__setattr__(self, name, value)
        
    
    def _encrypt_password(self, value):
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self._aes_key, AES.MODE_CFB, iv)
        msg = cipher.encrypt(value)
        return (iv, msg)
        
    def _decrypt_password(self, secure_text, iv):
        cipher = AES.new(self._aes_key, AES.MODE_CFB, iv)
        password =  cipher.decrypt(secure_text)
        return password.decode('utf-8')
    
    def save(self):
        """Save this record to the database."""
        # encrypt the password before saving, with a new iv
        iv, en_password = self._encrypt_password(self.db_password)
        plain_password = self.db_password
        self.db_password = en_password
        self.password_aes_iv = iv
        
        
        skip_attrs = ['member_classes', 'connection_settings', 'name', 'database_defaults', 'connection']
        
        HistoriaRecord.save(self)

        self.db_password = plain_password
        self._dirty = False
    
    def load(self, recordID):
        """Load record from the database."""
        super().load(recordID)
        
        # decrypt the password from the database
        self.db_password = self._decrypt_password(self.db_password, self.password_aes_iv)
        self._dirty = False

if __name__ == '__main__':
    import unittest
    
    import tests.test_user_db
    
    localtests = unittest.TestLoader().loadTestsFromModule(tests.test_user_db)
    unittest.TextTestRunner(verbosity=2).run(localtests)
