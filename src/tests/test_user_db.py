#!/usr/bin/env python3
# encoding: utf-8
"""
test_user_db.py

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

import unittest
import logging, sys

import mysql.connector

from database import settings
from database import core_data_objects
from database import exceptions
from database import user_db


class TestUserDatabase(unittest.TestCase):
    
    def setUp(self):
        self.testDBName = "historia_test"
        self.default_settings = {
          'user': 'historia_root',
          'password': 'historia',
          'host': '127.0.0.1',
          'database': '',
          'raise_on_warnings': False
        }
        
    def test_00_classVariables(self):
        """UserDatabase: classVariables"""
        self.assertEqual(user_db.HistoriaUserDatabase.type_label, "Historia User Database", "User DB label is wrong")
        self.assertEqual(user_db.HistoriaUserDatabase.machine_type, "historia_user_database", "User DB machine type is wrong")
    
    def test_10_construct(self):
        """UserDatabase: __init__()"""
        
        db = user_db.HistoriaUserDatabase(self.testDBName)
        
        self.assertIsInstance(db._logger, logging.Logger, "Default logger isn't a logger")
        self.assertEqual(db.name, self.testDBName, "Name passed to object didn't make it")
        self.assertIsNone(db._id, "ID should be none for databases")
        self.assertEqual(len(db.connection_settings), 5, "Incorrect number of DB settings")
        #self.assertEqual(len(db.member_classes), 3, "Incorrect number of member classes")
        self.assertEqual(db.database_defaults['charset'], 'utf8', 'User database should always use UTF-8')
        self.assertIsNone(db.connection, "Where did the database get a connection object already")
    
    def test_20_generate_SQL(self):
        """UserDatabase: generate database SQL statements"""
        
        db = user_db.HistoriaUserDatabase(self.testDBName)
        
        statements = db.generate_SQL()
        
        self.assertEqual(len(statements), (len(db.member_classes)*2)+2, "There should be 2 statements for each class + 2 for the database itself")
        
        self.assertIn(self.testDBName, statements[0][0], "DB name not in db create statement")
        self.assertIn(self.testDBName, statements[1][0], "DB name not in db use statement")
        
    
        
        
if __name__ == '__main__':
    unittest.main()