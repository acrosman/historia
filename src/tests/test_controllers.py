#!/usr/bin/env python3
# encoding: utf-8
"""
test_core_data.py

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

from internals import controllers

from database import core_data_objects
from database import system_db
from database import user

import tests.helper_functions


class TestHistoriaCoreController(unittest.TestCase):
    
    config_location = 'tests/test_config'
    
    @classmethod
    def setUpClass(cls):
        cls.config = tests.helper_functions.load_configuration(cls.config_location)

    def setUp(self):
        self.testDBName = TestHistoriaCoreController.config['database']["main_database"]
        self.default_settings = {
          'user': TestHistoriaCoreController.config['database']['user'],
          'password': TestHistoriaCoreController.config['database']['password'],
          'host': TestHistoriaCoreController.config['database']['host'],
          'database': '',
          'raise_on_warnings': TestHistoriaCoreController.config['database']["raise_on_warnings"]
        }
    
    def tearDown(self):
        # Make a good faith effort to clean up any database we created along the way.
        try:
            db = core_data_objects.HistoriaDatabase(None)
            db.connection_settings = self.default_settings
            db.connect()
            cur = db.cursor()
            cur.execute("DROP DATABASE `{0}`".format(self.testDBName))
            db.commit()
        except Exception as err:
            pass

    
    def test_00_construct(self):
        """HistoriaCoreController: Test __new__() and __init__()"""
        
        obj = controllers.HistoriaCoreController(config_location = 'tests/test_config')
        
        self.assertIsInstance(obj.logger, logging.Logger, "Default logger isn't a logger")
        self.assertIsInstance(obj.database, system_db.HistoriaSystemDatabase, "Database didn't initalize to None when none provided")
        self.assertIsNone(obj.interface, "Interface didn't initalize to None when none provided")
        self.assertEqual(obj.active_users, {}, "Active users dict isn't just an empty Dictionary")
        self.assertEqual(obj.active_user_databases, {}, "Active dabases dict isn't just an empty Dictionary")
    
    def test_10_create_database(self):
        """HistoriaCoreController: create_database(self, database_name, connection_settings, db_type = "user")"""
        # def create_database(self, database_name, connection_settings, db_type = "user"):
        
        obj = controllers.HistoriaCoreController(config_location = 'tests/test_config')
        
        db = obj.create_database(self.testDBName, self.default_settings, db_type="system")
        
        self.assertIsInstance(db, system_db.HistoriaSystemDatabase)
        self.assertEqual(db.name, self.testDBName, "Database name isn't the value we provided")
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
        
    @unittest.expectedFailure
    def test_20_load_database(self):
        """HistoriaCoreController: load_database(self, database_name)"""
        # def load_database(self, database_name):

        obj = controllers.HistoriaCoreController(config_location = 'tests/test_config')
        db = obj.create_database(self.testDBName, self.default_settings, db_type="system")
        
        db2 = obj.load_database(self.testDBName)
        
        self.assertIsInstance(db2, system_db.HistoriaSystemDatabase, "Valid database object not returned.")
        self.assertTrue(db2.connected, "New database object not connected.")
        self.assertEqual(db2.name, self.testDBName, "New Database name doesn't match requested database name.")

    def test_30_authenticate_user(self):
        """HistoriaCoreController: authenticate_user()"""
        # def authenticate_user(self, user_name, password):
        obj = controllers.HistoriaCoreController(config_location = 'tests/test_config')
        db = obj.create_database(self.testDBName, self.default_settings, db_type="system")
        
        obj.database = db
        
        name = "Sir Robin of Camelot"
        password = "What... is the capital of Assyria"
        email = "sir.robin@camelot.gov.uk"
        
        u1 = user.HistoriaUser(db)
        u1.name = name
        u1.password = password
        u1.email = email
        u1.save()
        
        response = obj.authenticate_user(name, password)
        self.assertIsInstance(response, user.HistoriaUser, "Valid user not returned with valid creds.")
        self.assertEqual(u1, response, "Returned user isn't the user that created the record.")
        
        response = obj.authenticate_user(email, password)
        self.assertIsInstance(response, user.HistoriaUser, "Valid user not returned with valid creds.")
        self.assertEqual(u1, response, "Returned user isn't the user that created the record.")

        response = obj.authenticate_user(email, "I don't know that")
        self.assertFalse(response, "False not returned with invalid creds.")

        response = obj.authenticate_user("Nothing to see here", "I don't know that")
        self.assertFalse(response, "False not returned with invalid creds.")

        obj.database.disconnect()

    @unittest.expectedFailure
    def test_40_check_access(self):
        """HistoriaCoreController: check_access(self, user, database)"""
        self.fail("nothing to access yet")
        # def check_access(self, user, database):
    
    @unittest.expectedFailure
    def test_50_end_session(self):
        """HistoriaCoreController: end_session(self, user)"""
        # def end_session(self, user):
        self.fail("no sessions to end yet")
        