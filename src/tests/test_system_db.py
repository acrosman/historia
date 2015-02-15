#!/usr/bin/env python3
# encoding: utf-8
"""
test_system_db.py

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

import unittest
import logging, sys

import mysql.connector

from database import settings
from database import user
from database import core_data_objects
from database import exceptions
from database import system_db


class TestSystemDatabase(unittest.TestCase):
    
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
        """SystemDatabase: classVariables"""
        self.assertEqual(system_db.HistoriaSystemDatabase.type_label, "Historia System Database", "System DB label is wrong")
        self.assertEqual(system_db.HistoriaSystemDatabase.machine_type, "historia_system_database", "System DB machine type is wrong")
    
    def test_10_construct(self):
        """SystemDatabase: __init__()"""
        
        db = system_db.HistoriaSystemDatabase(self.testDBName)
        
        self.assertIsInstance(db._logger, logging.Logger, "Default logger isn't a logger")
        self.assertEqual(db.name, self.testDBName, "Name passed to object didn't make it")
        self.assertIsNone(db._id, "ID should be none for databases")
        self.assertEqual(len(db.connection_settings), 5, "Incorrect number of DB settings")
        self.assertEqual(len(db.member_classes), 2, "Incorrect number of member classes")
        self.assertEqual(db.database_defaults['charset'], 'utf8', 'System database should always use UTF-8')
        self.assertIsNone(db.connection, "Where did the database get a connection object already")
    
    def test_20_generate_SQL(self):
        """SystemDatabase: generate database SQL statements"""
        
        db = system_db.HistoriaSystemDatabase(self.testDBName)
        
        statements = db.generate_SQL()
        
        self.assertEqual(len(statements), (len(db.member_classes)*2)+2, "There should be 2 statements for each class + 2 for the database itself")
        
        self.assertIn(self.testDBName, statements[0][0], "DB name not in db create statement")
        self.assertIn(self.testDBName, statements[1][0], "DB name not in db use statement")
        
    
    def test_30_createDatabase(self):
        """SystemDatabase: Create a new database (self)"""
        db = system_db.HistoriaSystemDatabase(self.testDBName)
        db.connection_settings = self.default_settings
        
        db.createDatabase(db) #right now there is only one database avialble to create.
        
        # db should now exist and be connected to itself....let's find out.
        self.assertTrue(db.connected, "DB not connected after creating itself")

        cur = db.cursor()
        
        sql = "SHOW DATABASES;"
        cur.execute(sql)
        result = [tbl['Database'] for tbl in cur.fetchall()]
        self.assertIn(db.name, result, "My database doesn't appear to exist")
        
        sql = "SELECT DATABASE();"
        cur.execute(sql)
        result = cur.fetchall()
        self.assertEqual(db.name, result[0]['DATABASE()'], "Database in use is not me")
        
        sql = "SHOW TABLES;"
        cur.execute(sql)
        result = cur.fetchall()
        col = "Tables_in_{0}".format(db.name)
        class_names = [n.machine_type for n in db.member_classes]
        self.assertEqual(len(result), len(db.member_classes), "Wrong number of tables in database")
        for tbl in result:
            self.assertIn(tbl[col], class_names,"Table {0} not in my table list.".format(tbl[col]))
        
        
if __name__ == '__main__':
    unittest.main()