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
from database import user_db

import tests.helper_functions


class TestSystemDatabase(unittest.TestCase):

    config_location = 'tests/test_config'

    @classmethod
    def setUpClass(cls):
        cls.config = tests.helper_functions.load_configuration(cls.config_location)

    
    def setUp(self):
        self.config = TestSystemDatabase.config
        self.key_file = self.config['server']['aes_key_file']
        self.test_master_db_name = self.config['database']["main_database"]
        self.test_user_db_name = '_'.join([self.config['database']["user_database_name_prefix"], 'user_db'])
        self.default_settings = {
          'user': self.config['database']['user'],
          'password': self.config['database']['password'],
          'host': self.config['database']['host'],
          'database': '',
          'raise_on_warnings': self.config['database']["raise_on_warnings"]
        }
        
    
    def tearDown(self):
        try:
            # Make a good faith effort to clean up any database we created along the way.
            if self.db.connected:
                try:
                    cur = self.db.cursor()
                    cur.execute("DROP DATABASE IF EXISTS `{0}`".format(self.test_master_db_name))
                    self.db.commit()
                except Exception as err:
                    #Say something if we fail in the hopes some fool reads the output...
                    print("Unable to drop test database: {0} due to {1}".format(self.test_master_db_name, err))
                try:
                    cur.execute("DROP DATABASE IF EXISTS `{0}`".format(self.test_user_db_name))
                    self.db.commit()
                except Exception as err:
                    #Say something if we fail in the hopes some fool reads the output...
                    print("Unable to drop test database: {0} due to {1}".format(self.test_user_db_name, err))
                try:
                    cur.execute("DROP USER {0}@{1}".format(self.test_user_db_name[:16], self.db.local_address))
                    cur.execute("FLUSH PRIVILEGES")
                    self.db.commit()
                except Exception as err:
                    pass # This throws errors when the users doesn't exist.
                
                                    
                    
                self.db.disconnect()
        except:
            pass

    
    def test_00_classVariables(self):
        """SystemDatabase: classVariables"""
        self.assertEqual(system_db.HistoriaSystemDatabase.type_label, "Historia System Database", "System DB label is wrong")
        self.assertEqual(system_db.HistoriaSystemDatabase.machine_type, "historia_system_database", "System DB machine type is wrong")
    
    def test_05_staticMethods(self):
        """SystemDatabase: Random String generator"""
        length = 32
        
        randString = system_db.HistoriaSystemDatabase.str_generator(length)
        
        self.assertEqual(len(randString), length, "Wrong length string generated")
    
    def test_10_construct(self):
        """SystemDatabase: __init__()"""
        
        self.db = system_db.HistoriaSystemDatabase(self.test_master_db_name)
        
        self.assertIsInstance(self.db._logger, logging.Logger, "Default logger isn't a logger")
        self.assertEqual(self.db.name, self.test_master_db_name, "Name passed to object didn't make it")
        self.assertIsNone(self.db._id, "ID should be none for databases")
        self.assertEqual(len(self.db.connection_settings), 5, "Incorrect number of DB settings")
        self.assertEqual(len(self.db.member_classes), 3, "Incorrect number of member classes")
        self.assertEqual(self.db.database_defaults['charset'], 'utf8', 'System database should always use UTF-8')
        self.assertIsNone(self.db.connection, "Where did the database get a connection object already")
        self.assertEqual(self.db.local_address, 'localhost', "Local server address has incorrect default")
        
        self.db.local_address = self.config['database']['local_server_address']
        self.assertEqual(self.db.local_address, self.config['database']['local_server_address'], "Local server address not set correctly")
    
    def test_20_generate_SQL(self):
        """SystemDatabase: generate database SQL statements"""
        
        self.db = system_db.HistoriaSystemDatabase(self.test_master_db_name)
        
        statements = self.db.generate_database_SQL()
        
        self.assertEqual(len(statements), (len(self.db.member_classes)*2)+2, "There should be 2 statements for each class + 2 for the database itself")
        
        self.assertIn(self.test_master_db_name, statements[0][0], "DB name not in db create statement")
        self.assertIn(self.test_master_db_name, statements[1][0], "DB name not in db use statement")
        
    
    def test_30_createDatabase(self):
        """SystemDatabase: Create a new database"""
        self.db = system_db.HistoriaSystemDatabase(self.test_master_db_name)
        self.db.connection_settings = self.default_settings
        
        self.db.createDatabase(self.db) #right now there is only one database avialble to create.
        
        # db should now exist and be connected to itself....let's find out.
        self.assertTrue(self.db.connected, "DB not connected after creating itself")

        cur = self.db.cursor()
        
        sql = "SHOW DATABASES;"
        cur.execute(sql)
        result = [tbl['Database'] for tbl in cur.fetchall()]
        self.assertIn(self.db.name, result, "My database doesn't appear to exist")
        
        sql = "SELECT DATABASE();"
        cur.execute(sql)
        result = cur.fetchall()
        self.assertEqual(self.db.name, result[0]['DATABASE()'], "Database in use is not me")
        
        sql = "SHOW TABLES;"
        cur.execute(sql)
        result = cur.fetchall()
        col = "Tables_in_{0}".format(self.db.name)
        class_names = [n.machine_type for n in self.db.member_classes]
        self.assertEqual(len(result), len(self.db.member_classes), "Wrong number of tables in database")
        for tbl in result:
            self.assertIn(tbl[col], class_names,"Table {0} not in my table list.".format(tbl[col]))

    def test_40_createUserDatabase(self):
        """SystemDatabase: Create a new user database"""
        self.db = system_db.HistoriaSystemDatabase(self.test_master_db_name)
        self.db.connection_settings = self.default_settings
        self.db.createDatabase(self.db)

        # db should now exist and be connected to itself....let's find out.
        self.assertTrue(self.db.connected, "DB not connected after creating itself")
        
        # Create a user database
        udb = user_db.HistoriaUserDatabase(self.db, self.test_user_db_name, self.key_file)
        
        self.db.createDatabase(udb)
        
        self.assertTrue(udb.connected, "User database not connected after creation")
        self.assertEqual(udb.db_user, udb.name[:16], "User name for MySQL user not generated correctly.")
        cur = self.db.cursor()
        
        # Check for database
        sql = "SHOW DATABASES;"
        cur.execute(sql)
        result = [tbl['Database'] for tbl in cur.fetchall()]
        self.assertIn(udb.name, result, "User database doesn't appear to exist")
        
        # Check db user
        sql = "USE mysql"
        cur.execute(sql)
        sql = """SELECT `user`.`User` AS UserName, `db`.* 
                    FROM `user` LEFT JOIN `db` ON `user`.`User` = `db`.`User` 
                    WHERE `user`.`User` =  %(user)s AND `user`.`Password` = PASSWORD(%(password)s)"""
        cur.execute(sql,{'user':udb.db_user, 'password':udb.db_password})
        result = cur.fetchall()
        self.assertEqual(len(result), 1, "There should be one and one 1 reference for this user in MySQL")
        result = result[0]
        self.assertEqual(result['UserName'].decode(), udb.db_user, "Wrong user name set on new user (huh?)")
        self.assertEqual(result['User'].decode(), udb.db_user, "Wrong user name set on new user in db table (huh?)")
        self.assertEqual(result['Host'].decode(), self.db.local_address, "Wrong host set on new user")
        self.assertEqual(result['Db'].decode(), udb.name, "Wrong database used for new user's access (Crap)")
        yes_privs = ['Select_priv', 'Insert_priv','Update_priv','Delete_priv',
                     'Create_priv', 'Drop_priv', 'References_priv', 'Index_priv',
                     'Alter_priv','Create_tmp_table_priv', 'Lock_tables_priv',
                     'Create_view_priv','Show_view_priv','Create_routine_priv',
                     'Alter_routine_priv','Execute_priv','Event_priv','Trigger_priv']
        no_privs = ['Grant_priv']
        
        for priv in yes_privs:
            self.assertEqual(result[priv], 'Y', "User was not given: {0}".format(priv))
        for priv in no_privs:
            self.assertEqual(result[priv], 'N', "User was given: {0}".format(priv))
        
        # Check that udb is connected
        udb_cur = udb.cursor()
        sql = "SELECT DATABASE();"
        udb_cur.execute(sql)
        result = udb_cur.fetchall()
        self.assertEqual(udb.name, result[0]['DATABASE()'], "Database in use is not me")
        
        # Check structure
        sql = "SHOW TABLES;"
        udb_cur.execute(sql)
        result = udb_cur.fetchall()
        col = "Tables_in_{0}".format(udb.name)
        class_names = [n.machine_type for n in udb.member_classes]
        self.assertEqual(len(result), len(udb.member_classes), "Wrong number of tables in database")
        for tbl in result:
            self.assertIn(tbl[col], class_names,"Table {0} not in my table list.".format(tbl[col]))

        
        
if __name__ == '__main__':
    unittest.main()