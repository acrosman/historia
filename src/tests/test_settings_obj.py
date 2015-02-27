#!/usr/bin/env python3
# encoding: utf-8
"""
test_settigns_obj.py

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
from database import core_data_objects
from database import exceptions

import tests.helper_functions


class TestSettingRecord(unittest.TestCase):
    
    config_location = 'tests/test_config'
    
    @classmethod
    def setUpClass(cls):
        cls.config = tests.helper_functions.load_configuration(cls.config_location)

    def setUp(self):
        self.testdb_name = type(self).config['database']["main_database"]
        self.db = core_data_objects.HistoriaDatabase(self.testdb_name)
    
    def database_setup(self, withTables=False):
        self.default_settings = {
          'user': type(self).config['database']['user'],
          'password': type(self).config['database']['password'],
          'host': type(self).config['database']['host'],
          'database': '',
          'raise_on_warnings': type(self).config['database']["raise_on_warnings"]
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
            statements = settings.HistoriaSetting.generate_SQL()
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
        """HistoriaSetting: class variables"""
        self.assertEqual(settings.HistoriaSetting.type_label,"Historia Settings Record", "Label doesn't match expected value")
        self.assertEqual(settings.HistoriaSetting.machine_type,"historia_settings", "Machine Type doesn't match expected value")
        self.assertEqual(len(settings.HistoriaSetting._table_fields), 2,"Field count doesn't match expected")
        
    
    def test_10_construct(self):
        """HistoriaSetting: Constructor"""
        setting = settings.HistoriaSetting(self.db)
        
        self.assertIsInstance(setting, settings.HistoriaSetting, "Umm, yeah, that's a problem...")
        self.assertIsNone(setting.name, "Name attribute missing from new object")
        self.assertIsNone(setting.value, "Value attribute missing from new object")
        self.assertIsInstance(setting._logger, logging.Logger, "Default logger isn't a logger")
        self.assertFalse(setting._dirty, "Dirty bit is be clean to start")
        self.assertIs(setting.database, self.db, "Database isn't the one we sent over")
        self.assertIsInstance(setting.database, core_data_objects.HistoriaDatabase, "Database object isn't the right type (oops)")
        
        
    def test_05_generateSQL(self):
        """HistoriaSetting: generateSQL for the record's table"""
        statements = settings.HistoriaSetting.generate_SQL()

        self.assertIsInstance(statements, tuple, "Statements should come back as a tuple.")
        self.assertEqual(len(statements),2, "There should be two statements")
        self.assertEqual(statements[0][0],"DROP TABLE IF EXISTS `historia_settings`", "Openning of the first statement is wrong")
        self.assertIn(settings.HistoriaSetting.machine_type, statements[1][0], "table name not in the create table statement")

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
        """HistoriaSetting: __setattr__"""

        setting = settings.HistoriaSetting(self.db)

        with self.assertRaises(AttributeError):
            setting.bogus_field = "Junk Data"

        setting._anything = "ok"
        self.assertEqual(setting._anything, "ok", "Assignment of _ variables works fine...well not really")
        
        setting.name = "Eric"
        self.assertEqual(setting.name, "Eric", "Assignment of setting name failed.")
        self.assertEqual(-1, setting.id, "ID is still -1")
        setting.value = "John"
        self.assertEqual(setting.value, "John", "Assignment of setting name failed.")
        
    def test_15_internals(self):
        """HistoriaSetting: __eq__ and __ne__"""

        # Two HistoriaRecords are equal when they have the same ID and same type.
        s1 = settings.HistoriaSetting(self.db)
        s2 = settings.HistoriaSetting(self.db)
        hr = core_data_objects.HistoriaRecord(self.db)

        self.assertNotEqual(s1, s2, "By default a blank record is equal to nothing else")
        self.assertNotEqual(s1, s1, "By default a blank record is equal to nothing else...even itself")

        hr._id=100
        s1.name = "Eric"
        s2.name = "Eric"

        self.assertEqual(s1, s2, "With matched ID they report Not equal")
        self.assertNotEqual(hr, s2, "A generic is matching a setting")
        s2.name = "Graham"
        self.assertNotEqual(s1, s2, "With mismatched ID they report equal")


    def test_30_save(self):
        """HistoriaSetting: save()"""

        s1 = settings.HistoriaSetting(self.db)

        self.assertRaises(exceptions.DataConnectionError, s1.save)

        # Setup the database and try again.
        self.database_setup(withTables=True)
        
        self.assertRaises(exceptions.DataSaveError, s1.save)
        
        s1.name = "Graham"
        s1.value = "Chapman"
        self.assertTrue(s1._dirty, "Dirty bit not active but data changed")
        s1.save()
        
        self.assertFalse(s1._dirty, "Dirty bit active after save")
        self.assertNotEqual(s1.id, s1.name, "Record ID screwed up on save.")
        self.assertNotEqual(s1.id, -1, "Record ID still -1 after save.")

        # Now let's go see if it's really there
        select = ("SELECT * FROM `historia_settings`",{})
        result = self.db.execute_select(select)

        self.assertEqual(len(result), 1, "There should be 1 and only 1 entry in the table.")
        self.assertEqual(result[0]['name'], s1.name, "name in the table should match the name on the record.")
        self.assertEqual(result[0]['value'].decode('utf-8'), s1.value, "value in the table should match the value on the record.")

    def test_40_load(self):
        """HistoriaSetting: load()"""

        self.database_setup(withTables=True)
        s1 = settings.HistoriaSetting(self.db)
        s1.name = "John"
        s1.value = "Cleese"
        s1.save()

        s2 = settings.HistoriaSetting(self.db)
        s2.load(s1.id)

        self.assertEqual(s1.name, s2.name, "IDs on original and loaded object don't match")
        self.assertFalse(s2._dirty, "The dirty bit is wrong after load.")
        self.assertEqual(s2, s1, "The two copies of the record should consider themselves equal.")

    def test_50_delete(self):
        """HistoriaSetting: delete()"""

        self.database_setup(withTables=True)
        s1 = settings.HistoriaSetting(self.db)
        s1.name = "John"
        s1.value = "Cleese"
        s1.save()

        s1.delete()

        # Now let's go see if it's really there
        select = ("SELECT * FROM `historia_settings`",{})
        result = self.db.execute_select(select)

        self.assertEqual(len(result), 0, "There should nothing in the table now.")
        self.assertEqual(-1, s1.id, "The ID should reset to -1")
    
if __name__ == '__main__':
    unittest.main()