#!/usr/bin/env python3
# encoding: utf-8
"""
test_user.py

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
import logging, sys, datetime

import bcrypt
import mysql.connector

from database import user
from database import core_data_objects
from database import exceptions

import tests.helper_functions

class TestUser(unittest.TestCase):
    
    config_location = 'tests/test_config'
    
    @classmethod
    def setUpClass(cls):
        cls.config = tests.helper_functions.load_configuration(cls.config_location)


    def setUp(self):
        self.testdb_name = "historia_testdb"
        self.db = core_data_objects.HistoriaDatabase(self.testdb_name)
    
    def database_setup(self, withTables=False):
        self.default_settings = {
          'user': TestUser.config['database']['user'],
          'password': TestUser.config['database']['password'],
          'host': TestUser.config['database']['host'],
          'database': '',
          'raise_on_warnings': TestUser.config['database']["raise_on_warnings"]
        }
        
        statements = self.db.generate_database_SQL()
        self.db.connection_settings = self.default_settings
        self.db.connect()
        cur = self.db.cursor()
        
        for state in statements:
            try:
                cur.execute(state[0], state[1])
                self.db.commit()
            except mysql.connector.Error as err:
                self.fail("Unable to create testing database: {0} \n while executing: {1}".format(err, state[0]))
        
        if withTables:
            statements = user.HistoriaUser.generate_SQL()
            for state in statements:
                try:
                    cur.execute(state[0], state[1])
                    self.db.commit()
                except mysql.connector.Error as err:
                    self.fail("Unable to create testing database: {0} \n while executing: {1}".format(err, state[0]))
        
        
    
    def tearDown(self):
        # Make a good faith effort to clean up any database we created along the way.
        if self.db.connected:
            try:
                cur = self.db.cursor()
                cur.execute("DROP DATABASE `{0}`".format(self.testdb_name))
                self.db.commit()
                self.db.disconnect()
            except Exception as err:
                #Say something if we fail in the hopes some fool reads the output...
                print("Unable to drop test database: {0} due to {1}".format(self.testdb_name, err))
        
    def test_00_classVars(self):
        """HistoriaUser: class variables"""
        self.assertEqual("Historia User", user.HistoriaUser.type_label, "Label not what was expected")
        self.assertEqual(user.HistoriaUser.machine_type,"historia_user", "Machine name not the expected value")
        self.assertEqual(len(user.HistoriaUser._table_fields), 9,"Wrong number fo fields in field list")
        
    
    def test_10_construct(self):
        """HistoriaUser: Constructor"""
        
        hu = user.HistoriaUser(self.db)
        
        self.assertIsInstance(hu, user.HistoriaUser, "Umm, yeah, that's a problem...")
        self.assertEqual(hu.id,-1, "ID not -1")
        self.assertIsNone(hu.name, "Name attribute missing from new object")
        self.assertIsNone(hu.email, "email attribute missing from new object")
        self.assertIsNone(hu.password, "password attribute missing from new object")
        self.assertIsNone(hu.modified, "modified attribute missing from new object")
        self.assertIsNone(hu.created, "created attribute missing from new object")
        self.assertIsNone(hu.last_access, "last_access attribute missing from new object")
        self.assertIsNone(hu.enabled, "enabled attribute missing from new object")
        self.assertIsNone(hu.admin, "admin attribute missing from new object")
        self.assertIsInstance(hu._logger, logging.Logger, "Default logger isn't a logger")
        self.assertFalse(hu._dirty, "Dirty bit is be clean to start")
        self.assertIs(hu.database, self.db, "Database isn't the one we sent over")
        self.assertIsInstance(hu.database, core_data_objects.HistoriaDatabase, "Database object isn't the right type (oops)")
        
        
        
    def test_05_generateSQL(self):
        """HistoriaUser: generateSQL for the record's table"""
        statements = user.HistoriaUser.generate_SQL()

        self.assertIsInstance(statements, tuple, "Statements should come back as a tuple.")
        self.assertEqual(len(statements),2, "There should be two statements")
        self.assertEqual(statements[0][0],"DROP TABLE IF EXISTS `{0}`".format(user.HistoriaUser.machine_type), "Openning of the first statement is wrong")
        self.assertIn(user.HistoriaUser.machine_type, statements[1][0], "table name not in the create table statement")

        # We have the statements, let's try to use them
        self.database_setup()
        cur = self.db.cursor()
        for state in statements:
            try:
                cur.execute(state[0], state[1])
                self.db.commit()
            except mysql.connector.Error as err:
                self.fail("Unable to create testing database: {0} \n while executing: {1}".format(err, state[0]))
        

    def test_10_internals(self):
        """HistoriaUser: __setattr__"""
        hu = user.HistoriaUser(self.db)

        with self.assertRaises(AttributeError):
            hu.bogus_field = "Junk Data"
        
        attrs = ['email', 'name', 'created', 'last_access', 'password']
        
        # All of the listed fields on a User should raise a ValueError when they are fed an integer
        for attr in attrs:
            with self.assertRaises(ValueError):
                setattr(hu, attr, 123243)
            
        
        hu._anything = "ok"
        self.assertEqual(hu._anything, "ok", "Assignment of _ variables works fine...except that they fail all the time")
        
        current_stamp = datetime.datetime.now()
        hu.name = "Eric"
        hu.password = "Super Secret"
        hu.email = "eric@python.co.uk"
        hu.created = current_stamp
        hu.last_access = current_stamp
        hu.enabled = True
        hu.admin = False
        self.assertEqual(-1, hu.id, "ID is still -1")
        self.assertEqual(hu.name, "Eric", "Assignment of setting name failed.")
        self.assertNotEqual(hu.password, "Super Secret", "Plain text passwords are evil.")
        self.assertEqual(hu.email, "eric@python.co.uk", "Assignment of setting email failed.")
        self.assertEqual(hu.created, current_stamp, "Assignment of setting created timestamp failed.")
        self.assertEqual(hu.last_access, current_stamp, "Assignment of setting access timestamp failed.")
        self.assertEqual(hu.enabled, True, "Assignment of setting enabled failed.")
        self.assertEqual(hu.admin, False, "Assignment of setting admin failed.")
        
        # check password encryption bypass
        hu._password = "my weak password"
        self.assertEqual(hu.password, "my weak password",  "Password encryption bypass failed")
        self.assertFalse(hasattr(hu, '_password'), "Password bypass still created an _password attribute")
        
        # Check that @ is banned from the name column
        with self.assertRaises(ValueError):
            setattr(hu, 'name', "some@thing.com")
        
        
    def test_20_password(self):
        """HistoriaUser: Test password comparison"""
        hu = user.HistoriaUser(self.db)
        
        sample_pass = "Super Secret Password"
        
        hu.password = sample_pass
        
        self.assertNotEqual(hu.password, sample_pass, "Password failed to hash")
        self.assertTrue(hu.checkPassword(sample_pass), "Password checking failed")
        

    def test_30_save(self):
        """HistoriaUser: save()"""
        hu = user.HistoriaUser(self.db)

        self.assertRaises(exceptions.DataConnectionError, hu.save)

        # Setup the database and try again.
        self.database_setup(withTables=True)
        
        self.assertRaises(exceptions.DataSaveError, hu.save)
        
        current_stamp = datetime.datetime.now()
        hu.name = "Eric"
        hu.password = "Super Secret"
        hu.email = "eric@python.co.uk"
        hu.created = current_stamp
        hu.last_access = current_stamp
        hu.enabled = True
        hu.admin = False
        self.assertTrue(hu._dirty, "Dirty bit not active but data changed")
        hu.save()
        
        self.assertFalse(hu._dirty, "Dirty bit active after save")
        self.assertNotEqual(hu.id, -1, "Record ID still -1 after save.")

        # Now let's go see if it's really there
        select = ("SELECT * FROM `historia_user`",{})
        result = self.db.execute_select(select)

        self.assertEqual(len(result), 1, "There should be 1 and only 1 entry in the table.")
        self.assertEqual(result[0]['name'], hu.name, "name in the table should match the name on the record.")
        self.assertEqual(result[0]['password'], hu.password, "password in the table should match the one on the record.")        
        self.assertEqual(result[0]['email'], hu.email, "email in the table should match the one on the record.")        
        self.assertAlmostEqual(result[0]['created'], hu.created, delta=datetime.timedelta(seconds=1), msg="created in the table should match the one on the record.")        
        self.assertAlmostEqual(result[0]['last_access'], hu.last_access,  delta=datetime.timedelta(seconds=1), msg="last_access in the table should match the one on the record.")        
        self.assertEqual(result[0]['enabled'], hu.enabled, "enabled in the table should match the one on the record.")        
        self.assertEqual(result[0]['admin'], hu.admin, "admin in the table should match the one on the record.")        
        self.assertNotEqual(result[0]['modified'], hu.modified, "modified in the table should not match the one on the record since that was setup by MySQL.")
        
    def test_33_save(self):
        """HistoriaUser: save() with only the minimum required settings"""
        hu = user.HistoriaUser(self.db)

        self.assertRaises(exceptions.DataConnectionError, hu.save)

        # Setup the database and try again.
        self.database_setup(withTables=True)

        self.assertRaises(exceptions.DataSaveError, hu.save)

        current_stamp = datetime.datetime.now()
        hu.name = "Eric"
        hu.password = "Super Secret"
        hu.email = "eric@python.co.uk"
        hu.save()

        self.assertFalse(hu._dirty, "Dirty bit active after save")
        self.assertNotEqual(hu.id, -1, "Record ID still -1 after save.")

        # Now let's go see if it's really there
        select = ("SELECT * FROM `historia_user`",{})
        result = self.db.execute_select(select)

        self.assertEqual(len(result), 1, "There should be 1 and only 1 entry in the table.")
        self.assertEqual(result[0]['name'], hu.name, "name in the table should match the name on the record.")
        self.assertEqual(result[0]['password'], hu.password, "password in the table should match the one on the record.")        
        self.assertEqual(result[0]['email'], hu.email, "email in the table should match the one on the record.")        
        self.assertEqual(result[0]['enabled'], 1, "enabled in the table should match the one on the record.")        
        self.assertEqual(result[0]['admin'], 0, "admin in the table should match the one on the record.")        
        
    def test_40_load(self):
        """HistoriaSetting: load()"""
        self.database_setup(withTables=True)
        hu1 = user.HistoriaUser(self.db)
        current_stamp = datetime.datetime.now()
        test_pass = "Super Secret Correct Horse Battery Staple"
        hu1.name = "Eric"
        hu1.password = test_pass
        hu1.email = "eric@python.co.uk"
        hu1.created = current_stamp
        hu1.last_access = current_stamp
        hu1.enabled = True
        hu1.admin = False
        hu1.save()

        hu2 = user.HistoriaUser(self.db)
        hu2.load(hu1.id)

        self.assertEqual(hu1.id, hu2.id, "IDs on original and loaded object don't match")
        self.assertFalse(hu2._dirty, "The dirty bit is wrong after load.")
        self.assertEqual(hu2, hu1, "The two copies of the record should consider themselves equal.")
        self.assertEqual(hu2.name, hu1.name, "name in the table should match the name on the record.")
        self.assertEqual(hu2.password, hu1.password, "password in the table should match the one on the record.")        
        self.assertEqual(hu2.email, hu1.email, "email in the table should match the one on the record.")        
        self.assertAlmostEqual(hu2.created, hu1.created, delta=datetime.timedelta(seconds=1), msg="created in the table should match the one on the record.")        
        self.assertAlmostEqual(hu2.last_access, hu1.last_access,  delta=datetime.timedelta(seconds=1), msg="last_access in the table should match the one on the record.")        
        self.assertEqual(hu2.enabled, hu1.enabled, "enabled in the table should match the one on the record.")        
        self.assertEqual(hu2.admin, hu1.admin, "admin in the table should match the one on the record.")        
        self.assertNotEqual(hu2.modified, hu1.modified, "modified in the table should not match the one on the record since that was setup by MySQL.")

    def test_50_delete(self):
        """HistoriaSetting: delete()"""
        self.database_setup(withTables=True)
        hu1 = user.HistoriaUser(self.db)
        current_stamp = datetime.datetime.now()
        test_pass = "Super Secret Correct Horse Battery Staple"
        hu1.name = "Eric"
        hu1.password = test_pass
        hu1.email = "eric@python.co.uk"
        hu1.created = current_stamp
        hu1.last_access = current_stamp
        hu1.enabled = True
        hu1.admin = False
        hu1.save()

        hu1.delete()

        # Now let's go see if it's really there
        select = ("SELECT * FROM `historia_user`",{})
        result = self.db.execute_select(select)

        self.assertEqual(len(result), 0, "There should nothing in the table now.")
        self.assertEqual(-1, hu1.id, "The ID should reset to -1")
    
if __name__ == '__main__':
    unittest.main()