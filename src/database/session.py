#!/usr/bin/env python3
# encoding: utf-8
"""
session.py

Created by Aaron Crosman on 2015-02-10.

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
import ssl
import uuid

from .core_data_objects import *
from .exceptions import *


class HistoriaSession(HistoriaRecord):

    type_label        = "Historia Session"
    machine_type      = "historia_session"
    _table_fields      = {'sessionid': {
                                'type':       'varchar',
                                'length': '36',
                                'allow_null': False,
                                'index':      { 'type':'UNIQUE', 'fields': ('sessionid',)},
                                'order': 1
                            },
                            'userid': {
                                'type':       'int',
                                'length': '11',
                                'allow_null': False,
                                'index':      { 'type':'BASIC', 'fields': ('userid',)},
                                'order': 2
                            },
                            'created':{
                                'type':'datetime',
                                'allow_null': False,
                                'default': None,
                                'order': 4
                            },
                            'last_seen':{
                                'type':'datetime',
                                'allow_null': True,
                                'default': None,
                                'order': 5
                            },
                            'ip':{
                                'type':'varchar',
                                'length': '32',
                                'allow_null':False,
                                'default':None,
                                'order':3
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
        if self.sessionid == None:
            return False
        else:
            try:
                if self.machine_type == other.machine_type:
                    return self.sessionid == other.sessionid
                else:
                    return False
            except AttritbuteError:
                return False

    def __ne__(self, other):
        if self.sessionid == None:
            return True
        else:
            try:
                if self.machine_type == other.machine_type:
                    return self.sessionid != other.sessionid
                else:
                    return True
            except AttritbuteError:
                return True


    def new_id(self):
        self.sessionid = str(uuid.UUID(bytes=ssl.RAND_bytes(16)))
        return self.sessionid

    # Overloaded to make sure we update the last_seen stamp
    def save(self):
        self.last_seen = datetime.datetime.now()
        super().save()

    # Overloaded to make sure we get the right settings without ID in use
    def load(self, recordID):
        super().load(recordID)
        self._id = self.sessionid
        self._dirty = False

    # Overloaded since session doesn't use primary key.
    def _generate_select_SQL(self, session_id):

        fields = {'sessionid': session_id}
        statement = "SELECT * FROM `{0}` WHERE `sessionid` = %({1})s".format(self.machine_type, 'sessionid')

        return (statement, fields)

    # Overloaded since session doesn't use primary key.
    def _generate_update_SQL(self):

        fields = {}
        primary = ''

        statement = "UPDATE `{0}` SET ".format(self.machine_type)

        for field in self._table_fields:
            if 'default' not in self._table_fields[field]:
                self._table_fields[field]['default'] = None

            if 'index' in self._table_fields[field]:
                if self._table_fields[field]['index']['type'] == 'PRIMARY':
                    primary = field

            if self._table_fields[field]['default'] =='AUTO_INCREMENT':
                continue # Don't touch auto fields

            if self._table_fields[field]['type'] == 'timestamp':
                continue # timestamps should be set to care for themselves.

            fields[field] = getattr(self, field)
            statement += "`{0}` = %({1})s,".format(field, field)

        statement = statement[:-1] + " WHERE `sessionid` = %(sessionid)s"
        fields['sessionid'] = self.sessionid

        return (statement, fields)



if __name__ == '__main__':
    import unittest

    import tests.test_settings

    localtests = unittest.TestLoader().loadTestsFromModule(tests.test_settings_obj)
    unittest.TextTestRunner(verbosity=2).run(localtests)
