#!/usr/local/bin/python3
# encoding: utf-8
"""
system_db.py

Created by Aaron Crosman on 2015-01-24.

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
from .settings import *
from .user import *
from .exceptions import *


class HistoriaSystemDatabase(HistoriaDatabase):
    type_label = "Historia System Database"
    machine_type = "historia_system_database"
    
    def __init__(self, database_name):
        super().__init__(database_name)
        
        self.member_classes = [
            HistoriaSetting,
            HistoriaUser
        ]
        
    def createDatabase(self, database):
        """Create a database, either a system database or a user database."""
        statements = database.generate_SQL()
        
        if not self.connected:
            self.connect()
        
        cur = self.cursor()
        
        for statement, params in statements:
            try:
                cur.execute(statement, params)
            except mysql.connector.Error as err:
                raise DatabaseCreationError("Unable to create new database: {0}".format(err))
        
        # A use database statement was run during the creation of the other database, now switch to yourself.
        sql = "USE `{0}`".format(self.name)
        cur.execute(sql, {})
        

if __name__ == '__main__':
    import unittest
    
    import tests.test_system_db
    
    localtests = unittest.TestLoader().loadTestsFromModule(tests.test_system_db)
    unittest.TextTestRunner(verbosity=2).run(localtests)
