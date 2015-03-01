#!/usr/bin/env python3
# encoding: utf-8
"""
test_controllers.py

Created by Aaron Crosman on 2015-02-02.

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
import json

import mysql.connector

from database import core_data_objects
from database import exceptions

import tests.helper_functions


class TestDataObject(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_1_new(self):
        """HistoriaDataObject: Test __new__()"""
        
        obj = core_data_objects.HistoriaDataObject()
        
        self.assertIsInstance(obj, core_data_objects.HistoriaDataObject, "DataObject is not the right type")
        self.assertEqual(obj.id, -1, "Default id is wrong")
        self.assertEqual(obj._id, -1, "Default  _id is wrong (and doesn't appear to match id")
        self.assertIsInstance(obj._logger, logging.Logger, "Default logger isn't a logger")
    
    def test_2_id(self):
        """HistoriaDataObject: test id control"""
        
        obj = core_data_objects.HistoriaDataObject()
        
        self.assertEqual(obj.id, obj._id, "id and _id don't match")
        
        obj._id = 13
        self.assertEqual(obj.id, 13, "id didn't update correct when _id changed")
        

class TestDatabase(unittest.TestCase):

    config_location = 'tests/test_config'

    @classmethod
    def setUpClass(cls):
        cls.config = tests.helper_functions.load_configuration(cls.config_location)

    def setUp(self):
        self.config = TestDatabase.config
        self.testdb_name = self.config['database']["main_database"]
        self.default_settings = {
          'user': self.config['database']['user'],
          'password': self.config['database']['password'],
          'host': self.config['database']['host'],
          'database': '',
          'raise_on_warnings': self.config['database']["raise_on_warnings"]
        }
        
    
    def tearDown(self):
        # Make a good faith effort to clean up any database we created along the way.
        try:
            db = core_data_objects.HistoriaDatabase(None)
            db.connection_settings = self.default_settings
            db.connect()
            cur = db.cursor()
            cur.execute("DROP DATABASE `{0}`".format(self.testdb_name))
            db.commit()
        except Exception as err:
            pass
    
    def prep_execute_test_tables(self):
        db = core_data_objects.HistoriaDatabase(self.testdb_name)
        statements = db.generate_database_SQL()
        db.connection_settings = self.default_settings
        db.connect()
        cur = db.cursor()
        self.test_table = "test"
        # Convert to list for editing
        statements = list(statements)
        statements += (('USE `{0}`'.format(self.testdb_name),{}),)
        statements += (("CREATE TABLE `{0}` (`id` int(11) unsigned NOT NULL AUTO_INCREMENT,`val` varchar(128) NOT NULL DEFAULT '',PRIMARY KEY (`id`)) ENGINE=InnoDB DEFAULT CHARSET=utf8;".format(self.test_table), {}),)
        
        for state in statements:
            try:
                cur.execute(state[0], state[1])
                db.commit()
            except mysql.connector.Error as err:
                print("Unable to create testing database and required tables: {0} \n while executing: {1}".format(err, state[0]), file=sys.stderr)
                return False
        
        return db
    
    def test_001_construct(self):
        """HistoriaDatabase: Create new """
        testName = "Historia_Tests"
        db = core_data_objects.HistoriaDatabase(testName)
        
        # Check that all default values are there and correct
        self.assertEqual(db.name, testName.lower(), "Name not assigned correctly during init")
        self.assertIsNone(db.id, "id not set to None during construction")
        self.assertIsInstance(db.connection_settings, dict, "Connections settings aren't a dict")
        self.assertIsInstance(db.member_classes, list, "member classes aren't a dict")
        self.assertIsInstance(db.database_defaults, dict, "database default settings aren't a dict")
        self.assertIsNone(db.connection, "connection not set to None during construction")
        self.assertIsInstance(db._logger, logging.Logger, "logger isn't actually a logger.")
        self.assertFalse(db.connected, "Database not reporting it self as disconnected")

    def test_005_internals(self):
        """HistoriaDatabase: Test name change handling  """
        testName = "Historia_Tests"
        db = core_data_objects.HistoriaDatabase(testName)

        # Check that all default values are there and correct
        self.assertEqual(db.name, testName.lower(), "Name not assigned correctly during init")

        with self.assertRaises(ValueError):
            db.name = "Junk Data"
        with self.assertRaises(ValueError):
            db.name = "valid+junk"
        with self.assertRaises(ValueError):
            db.name = 12341234
        
        db.name = "valid_database_name"
        self.assertEqual(db.name, "valid_database_name", "Name not assigned correctly after init")

    
    def test_010_connections(self):
        """HistoriaDatabase: Connect"""
        
        db = core_data_objects.HistoriaDatabase(None)
        db.connection_settings = self.default_settings
        db.connect()
        
        self.assertIsNotNone(db.connection, "Connection is still none after connecting")
        self.assertTrue(db.connected, "database object not reporting being connected after connect")
        self.assertTrue(db.connection.is_connected(), "Connection object is not reporting being connected (which means you have two problems most likely)")
        self.assertEqual(db.connected, db.connection.is_connected(), "Someone is lying about the connection status.")
        self.assertIsNotNone(db.connection.get_server_info(), "Got none when asking for server version.")
    
    def test_015_connections(self):
        """HistoriaDatabase: Connect and then Disconnect"""
        
        db = core_data_objects.HistoriaDatabase(None)
        db.connection_settings = self.default_settings
        db.connect()
        
        self.assertTrue(db.connected, "database object not reporting being connected after connect")
        
        db.disconnect()
        
        self.assertIsNotNone(db.connection, "Connection is none after disconnecting (there should still be an object kicking around)")
        self.assertFalse(db.connected, "database object reporting being connected after connect")
        self.assertFalse(db.connection.is_connected(), "Connection object is not reporting being connected (which means you have two problems most likely)")
        self.assertEqual(db.connected, db.connection.is_connected(), "Someone is lying about the connection status.")
    
    def test_020_cursors(self):
        """HistoriaDatabase: Get Cursor"""
        
        db = core_data_objects.HistoriaDatabase(None)
        db.connection_settings = self.default_settings
        db.connect()
        
        cur = db.cursor()
        
        self.assertIsNotNone(cur, "Cursor came back as none.")
        self.assertIsInstance(cur, mysql.connector.cursor.MySQLCursorDict, "Cursor is the wrong type: %s"%cur)
        
    def test_030_generateDBSQL(self):
        """HistoriaDatabase: generate SQL for database"""
        
        
        db = core_data_objects.HistoriaDatabase(self.testdb_name)
        statements = db.generate_database_SQL()
        
        self.assertIsNotNone(statements, "None returned instead of a list of statements")
        self.assertIsInstance(statements, tuple, "Statements should be a tuple of SQL and parameter paired tuples")
        self.assertEqual(len(statements), 2, "There should only be 2 statements in a default database")
        
        # Run in a loop in case the default statement count changes later
        for state in statements:
            self.assertIsInstance(state, tuple, "Not all statements were tuples")
            self.assertIsInstance(state[0], str, "First member of a statement wasn't a string")
            self.assertIsInstance(state[1], dict, "Second member of a statement wasn't a dict")
            
        self.assertDictEqual(statements[0][1],{}, "Second member isn't empty (it's all meta data that can't be escaped safely later)")
        self.assertIn(self.testdb_name, statements[0][0], "Test database name failed to pass into create string.")
        self.assertEqual(statements[0][0][:29], "CREATE DATABASE IF NOT EXISTS", "First statement doesn't start with a database creation statement")
        
        
        # Now we try to connect and actually run the statements that came back.
        db.connection_settings = self.default_settings
        db.connect()
        cur = db.cursor()
        
        for state in statements:
            try:
                cur.execute(state[0], state[1])
                db.commit()
            except mysql.connector.Error as err:
                self.fail("Database Creation Failed: {0}".format(err))
        
    
    def test_040_executes(self):
        """HistoriaDatabase: Test Insert Statement"""
        
        db = self.prep_execute_test_tables()
        
        if not db:
            self.fail("Unable to create database for testing.")
        
        statement = ("INSERT INTO {0} (`val`) VALUES (%s)".format(self.test_table), ['me'],)
        
        db.execute_insert(statement)
        
        cur = db.connection.cursor()
        sql = "SELECT * FROM {0}".format(self.test_table)
        cur.execute(sql)
        result = cur.fetchall()
        self.assertEqual(len(result), 1, "There should be one and only be one record to return")
        self.assertEqual(result[0][1], 'me', "Invalid returned value for the one and only field")
        
        # disconnect from database and make sure an error is raised when it should
        db.disconnect()
        self.assertRaises(exceptions.DataConnectionError, db.execute_insert, statement)
    
    def test_043_executes(self):
        """HistoriaDatabase: Test Select Statement"""
        db = self.prep_execute_test_tables()
        if not db:
            self.fail("Unable to create database for testing.")
        
        sample_data = "Seven is just right out"
        
        statement = ("INSERT INTO {0} (`val`) VALUES (%s)".format(self.test_table), [sample_data],)
        db.execute_insert(statement)
        
        select = ("SELECT * FROM {0} LIMIT 1".format(self.test_table),{})
        result = db.execute_select(select)
        
        self.assertEqual(len(result), 1, "There should be 1 and only 1 record to return")
        self.assertIsInstance(result, list, "Execute_select should be returning a list")
        self.assertIsInstance(result[0], dict, "Execute_select should be returning a list of dictionaries")
        self.assertEqual(result[0]['val'], sample_data, "Incorrect value returned")
        
        # disconnect from database and make sure an error is raised when it should
        db.disconnect()
        self.assertRaises(exceptions.DataConnectionError, db.execute_select, select)

    def test_047_executes(self):
        """HistoriaDatabase: Test Update Statement"""
        db = self.prep_execute_test_tables()
        if not db:
            self.fail("Unable to create database for testing.")

        sample_data = "I got better"
        sample_data2 = "Seven is just right out"

        statement = ("INSERT INTO {0} (`val`) VALUES (%s)".format(self.test_table), [sample_data],)
        db.execute_insert(statement)
        
        update_statement = ("INSERT INTO {0} (`val`) VALUES (%s)".format(self.test_table), [sample_data2],)
        db.execute_update(update_statement)
        
        select = ("SELECT * FROM {0} WHERE val = %s".format(self.test_table),[sample_data2])
        result = db.execute_select(select)

        self.assertEqual(len(result), 1, "There should be 1 and only 1 record to return")
        self.assertNotEqual(result[0]['val'], sample_data, "Incorrect value returned")
        self.assertEqual(result[0]['val'], sample_data2, "Incorrect value returned")

        # disconnect from database and make sure an error is raised when it should
        db.disconnect()
        self.assertRaises(exceptions.DataConnectionError, db.execute_update, update_statement)

    
class TestRecord(unittest.TestCase):
    
    config_location = 'tests/test_config'


    @classmethod
    def setUpClass(cls):
        cls.config = tests.helper_functions.load_configuration(cls.config_location)

    def setUp(self):
        self.config = TestRecord.config
        self.testdb_name = self.config['database']["main_database"]
        self.default_settings = {
          'user': self.config['database']['user'],
          'password': self.config['database']['password'],
          'host': self.config['database']['host'],
          'database': '',
          'raise_on_warnings': self.config['database']["raise_on_warnings"]
        }
        self.db = core_data_objects.HistoriaDatabase(self.testdb_name)
    
    def database_setup(self, withTables=False):
        
        statements = self.db.generate_database_SQL()
        self.db.connection_settings = self.default_settings
        self.db.connect()
        cur = self.db.cursor()
        # Convert to list for editing
        statements = list(statements)
        statements += (('USE `{0}`'.format(self.testdb_name),{}),)
        
        for state in statements:
            try:
                cur.execute(state[0], state[1])
                self.db.commit()
            except mysql.connector.Error as err:
                self.fail("Unable to create testing database: {0} \n while executing: {1}".format(err, state[0]))
        
        if (withTables):
            statements = core_data_objects.HistoriaRecord.generate_SQL()
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
    
    def test_000_class_vars(self):
        """HistoriaRecord: class defaults"""
        self.assertEqual(core_data_objects.HistoriaRecord.type_label, "Historia Generic Record", "Class has wrong label")
        self.assertEqual(core_data_objects.HistoriaRecord.machine_type, "historia_generic", "Class has wrong machine type")
        self.assertDictEqual(core_data_objects.HistoriaRecord._table_settings, { 'ENGINE': 'InnoDB','DEFAULT CHARSET': 'utf8'}, "Class has settings don't match expected")
        self.assertEqual(len(core_data_objects.HistoriaRecord._table_fields), 2, "There should be two fields on a generic record: id, value")
        self.assertIn('id', core_data_objects.HistoriaRecord._table_fields, "There should be an id field on generic record")
        self.assertIn('value', core_data_objects.HistoriaRecord._table_fields, "There should be a value field on a generic record")
        
    
    def test_001_construct(self):
        """HistoriaRecord: __init__"""
        
        hr = core_data_objects.HistoriaRecord(self.db)
        
        self.assertIsInstance(hr, core_data_objects.HistoriaRecord, "Yeah, so this should really never come up since an exception should have happened by now")
        self.assertEqual(hr.id, -1, "Default id is wrong")
        self.assertEqual(hr._id, -1, "Default  _id is wrong (and doesn't appear to match id")
        self.assertIsInstance(hr._logger, logging.Logger, "Default logger isn't a logger")
        self.assertFalse(hr._dirty, "Dirty bit is be clean to start")
        self.assertIs(hr.database, self.db, "Database isn't the one we sent over")
        self.assertIsInstance(hr.database, core_data_objects.HistoriaDatabase, "Database object isn't the right type (oops)")
        
    
    def test_005_generateSQL(self):
        """HistoriaRecord: generateSQL for the record's table"""
        statements = core_data_objects.HistoriaRecord.generate_SQL()
        
        self.assertIsInstance(statements, tuple, "Statements should come back as a tuple.")
        self.assertEqual(len(statements),2, "There should be two statements")
        self.assertEqual(statements[0][0],"DROP TABLE IF EXISTS `historia_generic`", "Openning of the first statement is wrong")
        self.assertIn(core_data_objects.HistoriaRecord.machine_type, statements[1][0], "table name not in the create table statement")
        
        # We have the statements, let's try to use them
        self.database_setup()
        cur = self.db.cursor()
        for state in statements:
            try:
                cur.execute(state[0], state[1])
                self.db.commit()
            except mysql.connector.Error as err:
                self.fail("Unable to create testing database: {0} \n while executing: {1}".format(err, state[0]))
        
    def test_010_internals(self):
        """HistoriaRecord: __setattr__"""
        
        hr = core_data_objects.HistoriaRecord(self.db)
        
        with self.assertRaises(AttributeError):
            hr.bogus_field = "Junk Data"
        
        hr._anything = "ok"
        self.assertEqual(hr._anything, "ok", "Assignment of _ variables works fine.")
    
    def test_015_internals(self):
        """HistoriaRecord: __eq__ and __ne__"""
        
        # Two HistoriaRecords are equal when they have the same ID and same type.
        hr1 = core_data_objects.HistoriaRecord(self.db)
        hr2 = core_data_objects.HistoriaRecord(self.db)
        
        self.assertNotEqual(hr1, hr2, "By default a blank record is equal to nothing else")
        self.assertNotEqual(hr1, hr1, "By default a blank record is equal to nothing else...even itself")
        
        hr1._id=100
        hr2._id=100
        
        self.assertEqual(hr1, hr2, "Even with changed ID they report Not equal")
        self.assertEqual(hr2, hr1, "Even with changed ID they report Not equal")
        
        hr2._id=10
        self.assertNotEqual(hr2, hr1, "Different IDs don't result in none-equal")
        
        # Since machine_type is a class level thing we can't test the conditionals until we have a subclass.
    
        
    def test_030_save(self):
        """HistoriaRecord: save()"""
        
        hr = core_data_objects.HistoriaRecord(self.db)
        
        self.assertRaises(exceptions.DataConnectionError, hr.save)
        
        # Setup the database and try again.
        self.database_setup(withTables=True)
        
        hr.save()
        
        self.assertEqual(hr.id, 1, "Record ID not updated on save.")
        
        # Now let's go see if it's really there
        select = ("SELECT * FROM `historia_generic`",{})
        result = self.db.execute_select(select)
        
        self.assertEqual(len(result), 1, "There should only be 1 entry in the table.")
        self.assertEqual(result[0]['id'], hr.id, "ID in the table should match the ID on the record.")
        
        # Call save again to trigger the update SQL code
        hr.value = "Changed"
        hr.save()
        select = ("SELECT * FROM `historia_generic`",{})
        result = self.db.execute_select(select)
        self.assertEqual(len(result), 1, "There should still only be 1 entry in the table.")
        self.assertEqual(result[0]['id'], hr.id, "ID in the table should match the ID on the record.")

        hr.value = "Change"
        hr.save()
        select = ("SELECT * FROM `historia_generic`",{})
        result = self.db.execute_select(select)
        self.assertEqual(len(result), 1, "There should still only be 1 entry in the table.")
        self.assertEqual(result[0]['id'], hr.id, "ID in the table should match the ID on the record.")


    def test_040_load(self):
        """HistoriaRecord: load()"""
        
        hr = core_data_objects.HistoriaRecord(self.db)
        self.database_setup(withTables=True)
        hr.save()
        
        hr2 = core_data_objects.HistoriaRecord(self.db)
        hr2.load(hr.id)
        
        self.assertEqual(hr2.id, hr.id, "IDs on original and loaded object don't match")
        self.assertFalse(hr2._dirty, "The dirty bit is wrong after load.")
        self.assertEqual(hr, hr2, "The two copies of the record should consider themselves equal.")
        
        # Try to load with bogus ID
        self.assertRaises(exceptions.DataLoadError, hr2.load, hr2.id+1)
        
        
    
    def test_045_load_and_save(self):
        """HistoriaRecord: use load() and save() a couple of times in a row to make sure we don't create extra records."""
    
        hr = core_data_objects.HistoriaRecord(self.db)
        self.database_setup(withTables=True)
        hr.save()
        
        hr2 = core_data_objects.HistoriaRecord(self.db)
        hr2.load(hr.id)
        hr2.value = "Changed"
        hr2.save()
        select = ("SELECT * FROM `historia_generic`",{})
        result = self.db.execute_select(select)
        self.assertEqual(len(result), 1, "There should still only be 1 entry in the table.")
        self.assertEqual(result[0]['id'], hr2.id, "ID in the table should match the ID on the record.")
    
    
    def test_050_delete(self):
        """HistoriaRecord: delete()"""
        
        hr = core_data_objects.HistoriaRecord(self.db)
        self.database_setup(withTables=True)
        hr.save()
        
        hr.delete()
        
        # Now let's go see if it's really there
        select = ("SELECT * FROM `historia_generic`",{})
        result = self.db.execute_select(select)
        
        self.assertEqual(len(result), 0, "There should nothing in the table now.")
        self.assertEqual(-1, hr.id, "The ID should reset to -1")
        
    def test_060_to_JSON(self):
        """HistoriaRecord: to_JSON()"""
        
        hr = core_data_objects.HistoriaRecord(self.db)
        
        hr.value = "Some Data"
        
        json_string = hr.to_JSON()
        
        self.assertIsInstance(json_string, str, "JSON string isn't a string")
        self.assertNotEqual(json_string, "", "JSON String is empty")
        
        parsed = json.loads(json_string)
        
        self.assertIsInstance(parsed, dict, "Parsed JSON doesn't resolve as a dict: {0}".format(json_string))
        self.assertIn(core_data_objects.HistoriaRecord.machine_type, parsed, "Machine type missing from parsed result")
        self.assertEqual(parsed[core_data_objects.HistoriaRecord.machine_type]["id"], hr.id, "ID in parsed dict doens't match original")
        self.assertEqual(parsed[core_data_objects.HistoriaRecord.machine_type]["value"], hr.value, "Value in parsed dict doens't match original")
        
    #TODO:  Add tests for the various _generate_*_SQL() methods

        
class TestSearchObject(unittest.TestCase):

    config_location = 'tests/test_config'


    @classmethod
    def setUpClass(cls):
        cls.config = tests.helper_functions.load_configuration(cls.config_location)

    def setUp(self):
        self.config = TestSearchObject.config
        self.testdb_name = self.config['database']["main_database"]
        self.default_settings = {
          'user': self.config['database']['user'],
          'password': self.config['database']['password'],
          'host': self.config['database']['host'],
          'database': '',
          'raise_on_warnings': self.config['database']["raise_on_warnings"]
        }
        self.db = core_data_objects.HistoriaDatabase(self.testdb_name)

    def database_setup(self, withTables=False):

        statements = self.db.generate_database_SQL()
        self.db.connection_settings = self.default_settings
        self.db.connect()
        cur = self.db.cursor()
        # Convert to list for editing
        statements = list(statements)
        statements += (('USE `{0}`'.format(self.testdb_name),{}),)

        for state in statements:
            try:
                cur.execute(state[0], state[1])
                self.db.commit()
            except mysql.connector.Error as err:
                self.fail("Unable to create testing database: {0} \n while executing: {1}".format(err, state[0]))

        if (withTables):
            statements = core_data_objects.HistoriaRecord.generate_SQL()
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

    def test_01_construct(self):
        """HistoriaRecord: __init__"""

        searcher = core_data_objects.HistoriaDatabaseSearch(self.db)

        self.assertIsInstance(searcher, core_data_objects.HistoriaDatabaseSearch, "Yeah, so this should really never come up since an exception should have happened by now")
        self.assertIs(searcher.database, self.db, "Database isn't the one we sent over")
        self.assertIsInstance(searcher.database, core_data_objects.HistoriaDatabase, "Database object isn't the right type (oops)")
        self.assertIsNone(searcher.search_scope, "Default scope is not None")
        self.assertEqual(searcher._return_fields, {}, "Default field list is not blank")
        self.assertEqual(searcher._joins,{}, "Default join dict not empty")
        self.assertEqual(searcher._conditions, [], "Default conditions list not empty")
        self.assertEqual(searcher._sorts, [], "Default sort list is empty")
        self.assertIsNone(searcher._limit, "Initial list is not None")
        self.assertIsNone(searcher.saved_results, "Default saved results not None")
    
        searcher = core_data_objects.HistoriaDatabaseSearch(self.db, "User")
        self.assertIs(searcher.search_scope, "User", "Search scope not assigned correctly during setup")
    
    def test_20_add_field(self):
        """HistoriaRecord: add_field(self, field_name)"""
        #def add_field(self, field_name):
        searcher = core_data_objects.HistoriaDatabaseSearch(self.db, "User")
        
        searcher.add_field('name')
        self.assertIn('name', searcher._return_fields, "field not added to field list")
        self.assertEqual(searcher._return_fields['name'], 'name', "Default alias wasn't the same as the field name")
        
        searcher.add_field('email', 'mail')
        self.assertIn('email', searcher._return_fields, "field not added to field list when alias given")
        self.assertEqual(searcher._return_fields['email'], 'mail', "Assigned alias wasn't the same as the one provided")
    
    
    def test_30_add_expression(self):
        """HistoriaRecord: add_expression(self, expression, values, alias=None)"""
        #def add_expression(self, expression, values, alias=None):
        searcher = core_data_objects.HistoriaDatabaseSearch(self.db, "User")
        
        searcher.add_expression('COUNT[{0}]',('email'), 'count_mail')
        self.assertIn('count_mail', searcher._return_fields, "expression not added to field list")
        self.assertEqual(searcher._return_fields['count_mail'], ('COUNT[{0}]',('email'), 'count_mail'), "Tuple values not in place")
        
    def test_40_add_join(self):
        """HistoriaRecord: add_join(self, main_field, table, table_field, operation = "=")"""
        #def add_join(self, main_field, table, table_field, operation = "="):
        
        searcher = core_data_objects.HistoriaDatabaseSearch(self.db, "User")
        
        searcher.add_join('id', 'user_database', 'uid')
        
        self.assertIn('user_database', searcher._joins, "join missing from join list.")
        self.assertEqual(searcher._joins['user_database'], ('id', 'uid', '='), "Expression not saved as expected")
        
        
    def test_50_add_condition(self):
        """HistoriaRecord: add_condition(self, field, value, comparison = "=", scope="AND")"""
        #def add_condition(self, field, value, comparison = "=", scope="AND"):
        
        searcher = core_data_objects.HistoriaDatabaseSearch(self.db, "User")
        
        searcher.add_condition('id', '1')
        
        self.assertEqual(searcher._conditions[0], ('id', '1', '=', 'AND'))
        
        searcher.add_condition('email', 'sir.robin@camelot.%', 'LIKE', "OR")
        
        self.assertEqual(searcher._conditions[1], ('email', 'sir.robin@camelot.%', 'LIKE', 'OR'))
        
        self.assertRaises(ValueError, searcher.add_condition,'email', 'sir.robin@camelot.%', 'LIKE', "NOPE")
        
        
    def test_60_add_sort(self):
        """HistoriaRecord: add_sort(self, field, direction="ASC")"""
        #def add_sort(self, field, direction="ASC"):
        
        searcher = core_data_objects.HistoriaDatabaseSearch(self.db, "User")
        
        searcher.add_sort('id')
        
        self.assertEqual(searcher._sorts[0], ('id', 'ASC'), "Adding ID sort failed to save as expected")
        
        searcher.add_sort('email', 'DESC')
        
        self.assertEqual(searcher._sorts[1], ('email', 'DESC'), "Adding email sort failed to save as expected")
        
        self.assertRaises(ValueError, searcher.add_sort,'email', "NOPE")
        
    def test_70_add_limit(self):
        """HistoriaRecord: add_limit(self, limit=None)"""
        #def add_limit(self, limit=None):
        searcher = core_data_objects.HistoriaDatabaseSearch(self.db, "User")
        
        searcher.add_limit(100)
        
        self.assertIs(searcher._limit, 100, "Limit did not set correctly to value")
        
        searcher.add_limit()
        self.assertIsNone(searcher._limit, "Limit did not set correctly to None")
        
        
    def test_80_generate_sql(self):
        """HistoriaRecord: _generate_sql(self)"""
        #def _generate_sql(self):
        searcher = core_data_objects.HistoriaDatabaseSearch(self.db, "User")
        
        searcher.add_field('id')
        searcher.add_field('name', "Real_Name")
        searcher.add_expression('COUNT[{0}]',('email'), 'count_mail')
        searcher.add_join('id', 'user_database', 'uid')
        searcher.add_condition('id', '1')
        searcher.add_condition('name', 'John')
        searcher.add_sort('id')
        searcher.add_limit(100)
        
        sql = searcher._generate_sql()
        
        # we can't really test this without a database (See next test), but we
        # can check a couple small things.
        self.assertIsInstance(sql, tuple, "_generate_sql didn't return a tuple of code and values")
        self.assertIsInstance(sql[0], str, "_generate_sql didn't return a string of code")
        self.assertNotEqual('', sql[0], "SQL is empty")
        self.assertEqual('SELECT', sql[0][:6], "SQL doesn't start with SELECT")
        
        
    def test_90_execute_search(self):
        """HistoriaRecord: execute_search(self)"""
        #def execute_search(self):
        value1 = "First"
        value2 = "Nope"
        searcher = core_data_objects.HistoriaDatabaseSearch(self.db, core_data_objects.HistoriaRecord.machine_type)
        self.database_setup(withTables=True)
        
        hr = core_data_objects.HistoriaRecord(self.db)
        hr2 = core_data_objects.HistoriaRecord(self.db)
        hr.value = value1
        hr.save()
        hr2.value = value2
        hr2.save()
        
        # Get me the second record
        searcher.add_field('id')
        searcher.add_field('value')
        searcher.add_condition('value', value2)
        
        results = searcher.execute_search()
        
        self.assertIsNotNone(results, "None returned from valid search")
        self.assertEqual(len(results), 1,"Wrong number of results")
        self.assertEqual(results[0]['id'], hr2.id,"Wrong ID value returned")
        self.assertEqual(results[0]['value'], value2,"Wrong value found")
        
        
        searcher = core_data_objects.HistoriaDatabaseSearch(self.db, core_data_objects.HistoriaRecord.machine_type)
        searcher.add_field('id')
        searcher.add_field('value')
        searcher.add_condition('id', '0', ">")
        results = searcher.execute_search()
        self.assertIsNotNone(results, "None returned from valid search")
        self.assertEqual(len(results), 2,"Wrong number of results")
        
        searcher = core_data_objects.HistoriaDatabaseSearch(self.db, core_data_objects.HistoriaRecord.machine_type)
        searcher.add_field('id')
        searcher.add_field('value')
        searcher.add_condition('id', '1')
        searcher.add_condition('id', '2', '=', 'OR')
        results = searcher.execute_search()
        self.assertIsNotNone(results, "None returned from valid search")
        self.assertEqual(len(results), 2,"Wrong number of results sql: {0} values: {1}".format(searcher._generate_sql()[0],searcher._generate_sql()[1]))
        
        
        searcher = core_data_objects.HistoriaDatabaseSearch(self.db, core_data_objects.HistoriaRecord.machine_type)
        searcher.add_field('id')
        searcher.add_field('value')
        searcher.add_expression('COUNT(`id`)')
        searcher.add_condition('id', '0', ">")
        results = searcher.execute_search()
        self.assertIsNotNone(results, "None returned from valid search")
        self.assertEqual(len(results), 1,"Wrong number of results")
        self.assertIsNotNone(results[0]['expression_2'], "Expression didn't return")
        

