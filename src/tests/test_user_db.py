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
import logging, sys, datetime

import mysql.connector

from database import settings
from database import core_data_objects
from database import exceptions
from database import user_db

import tests.helper_functions


class TestUserDatabase(unittest.TestCase):
    
    config_location = 'tests/test_config'
    
    @classmethod
    def setUpClass(cls):
        cls.config = tests.helper_functions.load_configuration(cls.config_location)
    
    def setUp(self):
        self.config = TestUserDatabase.config
        self.key_file = self.config['database']['aes_key_file']
        self.testDBName = self.config['database']["main_database"]
        self.default_settings = {
          'user': self.config['database']['user'],
          'password': self.config['database']['password'],
          'host': self.config['database']['host'],
          'database': '',
          'raise_on_warnings': self.config['database']["raise_on_warnings"]
        }
        self.db = core_data_objects.HistoriaDatabase(self.testDBName)
    
    def tearDown(self):
        try:
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
        except:
            pass
    
    def database_setup(self, withTables=False):

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
            statements = user_db.HistoriaUserDatabase.generate_SQL()
            for state in statements:
                try:
                    cur.execute(state[0], state[1])
                    self.db.commit()
                except mysql.connector.Error as err:
                    self.fail("Unable to create testing database: {0} \n while executing: {1}".format(err, state[0]))


    def test_00_classVariables(self):
        """UserDatabase: classVariables"""
        self.assertEqual(user_db.HistoriaUserDatabase.type_label, "Historia User Database", "User DB label is wrong")
        self.assertEqual(user_db.HistoriaUserDatabase.machine_type, "historia_user_database", "User DB machine type is wrong")

    def test_10_construct(self):
        """UserDatabase: __init__()"""
        
        db = user_db.HistoriaUserDatabase(self.testDBName, self.key_file)
        
        self.assertIsInstance(db._logger, logging.Logger, "Default logger isn't a logger")
        self.assertEqual(db.name, self.testDBName, "Name passed to object didn't make it")
        self.assertEqual(db._id, -1, "ID should be -1 for user databases")
        self.assertEqual(len(db.connection_settings), 5, "Incorrect number of DB settings")
        self.assertEqual(db.database_defaults['charset'], 'utf8', 'User database should always use UTF-8')
        self.assertIsNone(db.connection, "Where did the database get a connection object already")
    
    def test_15_internals(self):
        """UserDatabase: __setattr__"""
        #self.database_setup()
        udb = user_db.HistoriaUserDatabase(self.db, self.key_file)

        with self.assertRaises(AttributeError):
            udb.bogus_field = "Junk Data"

        attrs = ['db_name', 'db_user', 'db_address', 'created', 'last_record_update', 'last_login']

        # All of the listed fields on a User should raise a ValueError when they are fed an integer
        for attr in attrs:
            with self.assertRaises(ValueError):
                setattr(udb, attr, 123243)


        udb._anything = "ok"
        self.assertEqual(udb._anything, "ok", "Assignment of _ variables works fine...except that they fail all the time")

        current_stamp = datetime.datetime.now()
        udb.db_name = "monty_db"
        udb.db_user = "monty"
        udb.db_password = "Plain text password"
        udb.db_address = "127.0.0.1"
        udb.created = current_stamp
        udb.last_login = current_stamp
        udb.enabled = True
        self.assertEqual(-1, udb.id, "ID is still -1")
        self.assertEqual(udb.db_name, "monty_db", "Assignment of setting name failed.")
        self.assertEqual(udb.db_password, "Plain text password", "Assignment of password failed")
        self.assertEqual(udb.db_address, "127.0.0.1", "Assignment of setting address failed.")
        self.assertEqual(udb.created, current_stamp, "Assignment of setting created timestamp failed.")
        self.assertEqual(udb.last_login, current_stamp, "Assignment of setting access timestamp failed.")
        self.assertEqual(udb.enabled, True, "Assignment of setting enabled failed.")
        self.assertEqual(udb.db_user, 'monty', "Assignment of setting user failed.")
        
    def test_20_generate_DB_SQL(self):
        """UserDatabase: generate database SQL statements"""
        
        db = user_db.HistoriaUserDatabase(self.testDBName, self.key_file)
        
        statements = db.generate_database_SQL()
        
        self.assertEqual(len(statements), (len(db.member_classes)*2)+2, "There should be 2 statements for each class + 2 for the database itself")
        
        self.assertIn(self.testDBName, statements[0][0], "DB name not in db create statement")
        self.assertIn(self.testDBName, statements[1][0], "DB name not in db use statement")
        
    def test_25_generate_table_SQL(self):
        """UserDatabase: generateSQL for the record's table"""
        statements = user_db.HistoriaUserDatabase.generate_SQL()

        self.assertIsInstance(statements, tuple, "Statements should come back as a tuple.")
        self.assertEqual(len(statements),2, "There should be two statements")
        self.assertEqual(statements[0][0],"DROP TABLE IF EXISTS `{0}`".format(user_db.HistoriaUserDatabase.machine_type), "Openning of the first statement is wrong")
        self.assertIn(user_db.HistoriaUserDatabase.machine_type, statements[1][0], "table name not in the create table statement")

        # We have the statements, let's try to use them
        self.database_setup()
        cur = self.db.cursor()
        for state in statements:
            try:
                cur.execute(state[0], state[1])
                self.db.commit()
            except mysql.connector.Error as err:
                self.fail("Unable to create testing database: {0} \n while executing: {1}".format(err, state[0]))
        
    def test_30_save(self):
        """UserDatabase: save()"""
        udb = user_db.HistoriaUserDatabase(self.db, self.key_file)

        self.assertRaises(exceptions.DataConnectionError, udb.save)

        # Setup the database and try again.
        self.database_setup(withTables=True)
        
        self.assertRaises(exceptions.DataSaveError, udb.save)
        
        current_stamp = datetime.datetime.now()
        udb.db_name = "monty_db"
        udb.db_user = "monty"
        udb.db_address = "127.0.0.1"
        udb.db_password = "Plain text password"
        udb.created = current_stamp
        udb.last_login = current_stamp
        udb.enabled = True
        self.assertTrue(udb._dirty, "Dirty bit not active but data changed")
        udb.save()
        
        self.assertFalse(udb._dirty, "Dirty bit active after save")
        self.assertNotEqual(udb.id, -1, "Record ID still -1 after save.")

        # Now let's go see if it's really there
        select = ("SELECT * FROM `historia_user`",{})
        result = self.db.execute_select(select)

        self.assertEqual(len(result), 1, "There should be 1 and only 1 entry in the table.")
        self.assertEqual(result[0]['db_name'], udb.db_name, "name in the table should match the name on the record.")
        self.assertNotEqual(result[0]['db_password'], udb.db_password, "password in the table should not match the one on the record.")        
        self.assertEqual(result[0]['db_user'], udb.db_user, "db_user in the table should match the one on the record.")
        self.assertAlmostEqual(result[0]['created'], udb.created, delta=datetime.timedelta(seconds=1), msg="created in the table should match the one on the record.")        
        self.assertAlmostEqual(result[0]['last_login'], udb.last_login,  delta=datetime.timedelta(seconds=1), msg="last_login in the table should match the one on the record.")        
        self.assertEqual(result[0]['enabled'], udb.enabled, "enabled in the table should match the one on the record.")        
        self.assertEqual(result[0]['db_address'], udb.db_address, "db_address in the table should match the one on the record.")

    def test_40_load(self):
        """HistoriaSetting: load()"""
        self.database_setup(withTables=True)
        udb = user_db.HistoriaUserDatabase(self.db, self.key_file)
        current_stamp = datetime.datetime.now()
        udb.db_name = "monty_db"
        udb.db_user = "monty"
        udb.db_address = "127.0.0.1"
        udb.db_password = "Plain text password"
        udb.created = current_stamp
        udb.last_login = current_stamp
        udb.enabled = True
        self.assertTrue(udb._dirty, "Dirty bit not active but data changed")
        udb.save()

        udb2 = user_db.HistoriaUserDatabase(self.db)
        udb2.load(udb1.id)

        self.assertEqual(udb.id, udb2.id, "IDs on original and loaded object don't match")
        self.assertFalse(udb2._dirty, "The dirty bit is wrong after load.")
        self.assertEqual(udb2, udb, "The two copies of the record should consider themselves equal.")
        self.assertEqual(udb2.db_name, udb.db_name, "name in the table should match the name on the record.")
        self.assertEqual(udb2.db_password, udb.db_password, "password in the table should match the one on the record.")        
        self.assertEqual(udb2.db_user, udb.db_user, "db_user in the table should match the one on the record.")        
        self.assertAlmostEqual(udb2.created, udb.created, delta=datetime.timedelta(seconds=1), msg="created in the table should match the one on the record.")        
        self.assertAlmostEqual(udb2.last_login, udb.last_login,  delta=datetime.timedelta(seconds=1), msg="last_login in the table should match the one on the record.")        
        self.assertEqual(udb2.enabled, udb.enabled, "enabled in the table should match the one on the record.")        
        self.assertEqual(udb2.db_address, udb.db_address, "db_address in the table should match the one on the record.")        

    def test_50_delete(self):
        """HistoriaSetting: delete()"""
        self.database_setup(withTables=True)
        udb = user_db.HistoriaUserDatabase(self.db, self.key_file)
        current_stamp = datetime.datetime.now()
        udb.db_name = "monty_db"
        udb.db_user = "monty"
        udb.db_address = "127.0.0.1"
        udb.db_password = "Plain text password"
        udb.created = current_stamp
        udb.last_login = current_stamp
        udb.enabled = True
        self.assertTrue(udb._dirty, "Dirty bit not active but data changed")
        udb.save()

        udb.delete()

        # Now let's go see if it's really there
        select = ("SELECT * FROM `historia_user`",{})
        result = self.db.execute_select(select)

        self.assertEqual(len(result), 0, "There should nothing in the table now.")
        self.assertEqual(-1, udb.id, "The ID should reset to -1")
        
        
if __name__ == '__main__':
    unittest.main()