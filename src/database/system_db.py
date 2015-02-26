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

import sys, os
import random, string

from .core_data_objects import *
from .settings import *
from .user import *
from .session import *
from .user_db import *
from .exceptions import *



class HistoriaSystemDatabase(HistoriaDatabase):
    type_label = "Historia System Database"
    machine_type = "historia_system_database"
    
    def __init__(self, database_name):
        super().__init__(database_name)
        
        self.member_classes = [
            HistoriaSetting,
            HistoriaUser,
            HistoriaSession
        ]
        
        self.local_address = 'localhost'
        
    def createDatabase(self, database):
        """Create a database, either a system database or a user database."""
        if not self.connected:
            self.connect()
        
        cur = self.cursor()
        
        # User Databases need a user created, it will need access to the 
        # new database once that's complete.
        if database.machine_type == HistoriaUserDatabase.machine_type:
            new_user = database.name[:16] # MySQL has a hard limit of 16 characters
            new_pass = self.str_generator(32) #TODO: make this a setting that can be changed.
            user_sql = "CREATE USER '{0}'@'{1}' IDENTIFIED BY '{2}'".format(new_user, self.local_address, new_pass)
            try:
                cur.execute(user_sql)
            except mysql.connector.Error as err:
                raise DatabaseCreationError("Unable to create new database user: {0}".format(err))
            
        statements = database.generate_database_SQL()
        
        for statement, params in statements:
            try:
                cur.execute(statement, params)
            except mysql.connector.Error as err:
                raise DatabaseCreationError("Unable to create new database: {0}".format(err))
        
        # A use database statement was run during the creation of the other database, now switch to yourself.
        sql = "USE `{0}`".format(self.name)
        cur.execute(sql, {})
        
        # If this is a user database, make sure the user created above can access the new database.
        if database.machine_type == HistoriaUserDatabase.machine_type:
            user_grant_sql = "GRANT ALL ON {0}.* TO '{1}'@'{2}' ".format(database.name, new_user, self.local_address)
            cur.execute(user_grant_sql)
            database.db_password = new_pass
            database.db_user = new_user
            database.db_address = self.connection_settings['host']
        
        # Now make sure the other database is connected to itself.
        if not database.connected:
            database.connect()

        cur = database.cursor()
        sql = "USE `{0}`".format(database.name)
        cur.execute(sql, {})
    
    @staticmethod
    def str_generator(size=6, chars=string.ascii_letters + string.digits):
        return ''.join(random.SystemRandom().choice(chars) for _ in range(size))

if __name__ == '__main__':
    import unittest
    
    import tests.test_system_db
    
    localtests = unittest.TestLoader().loadTestsFromModule(tests.test_system_db)
    unittest.TextTestRunner(verbosity=2).run(localtests)
