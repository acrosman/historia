#!/usr/bin/env python3
# encoding: utf-8
"""
test_sessions.py

Created by Aaron Crosman on 2015-02-10.

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

from database import session
from database import core_data_objects
from database import exceptions


class TestUser(unittest.TestCase):
    def setUp(self):
        self.testdb_name = "historia_testdb"
        self.db = core_data_objects.HistoriaDatabase(self.testdb_name)
    
    def database_setup(self, withTables=False):
        self.default_settings = {
          'user': 'historia_root',
          'password': 'historia',
          'host': '127.0.0.1',
          'database': '',
          'raise_on_warnings': False
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
            statements = session.HistoriaSession.generate_SQL()
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
        """HistoriaSession: class variables"""
        self.assertEqual("Historia Session", session.HistoriaSession.type_label, "Label not what was expected")
        self.assertEqual(session.HistoriaSession.machine_type,"historia_session", "Machine name not the expected value")
        self.assertEqual(len(session.HistoriaSession._table_fields),5,"Wrong number fo fields in field list")
        
    
    def test_10_construct(self):
        """HistoriaSession: Constructor"""
        
        sess = session.HistoriaSession(self.db)
        
        self.assertIsInstance(sess, session.HistoriaSession, "Umm, yeah, that's a problem...")
        self.assertIsNone(sess.sessionid, "sessionid attribute missing from new object")
        self.assertIsNone(sess.userid, "userid attribute missing from new object")
        self.assertIsNone(sess.created, "created attribute missing from new object")
        self.assertIsNone(sess.last_seen, "last_seen attribute missing from new object")
        self.assertIsNone(sess.ip, "ip attribute missing from new object")
        self.assertIsInstance(sess._logger, logging.Logger, "Default logger isn't a logger")
        self.assertFalse(sess._dirty, "Dirty bit is be clean to start")
        self.assertIs(sess.database, self.db, "Database isn't the one we sent over")
        self.assertIsInstance(sess.database, core_data_objects.HistoriaDatabase, "Database object isn't the right type (oops)")
        
        
    def test_05_generateSQL(self):
        """HistoriaSession: generateSQL for the record's table"""
        statements = session.HistoriaSession.generate_SQL()

        self.assertIsInstance(statements, tuple, "Statements should come back as a tuple.")
        self.assertEqual(len(statements),2, "There should be two statements")
        self.assertEqual(statements[0][0],"DROP TABLE IF EXISTS `{0}`".format(session.HistoriaSession.machine_type), "Openning of the first statement is wrong")
        self.assertIn(session.HistoriaSession.machine_type, statements[1][0], "table name not in the create table statement")

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
        """HistoriaSession: __setattr__"""
        sess = session.HistoriaSession(self.db)

        with self.assertRaises(AttributeError):
            sess.bogus_field = "Junk Data"
        
        attrs = ['sessionid', 'created', 'last_seen', 'ip']
        
        # All of the listed fields on a User should raise a ValueError when they are fed an integer
        for attr in attrs:
            with self.assertRaises(ValueError):
                setattr(sess, attr, 123243)
            
        
        sess._anything = "ok"
        self.assertEqual(sess._anything, "ok", "Assignment of _ variables works fine...except that they fail all the time")
        
        current_stamp = datetime.datetime.now()
        sess.sessionid = "12354ABCDEF"
        sess.created = current_stamp
        sess.last_seen = current_stamp
        sess.userid = 123
        self.assertEqual(sess.sessionid, "12354ABCDEF", "Assignment of sessionid failed.")
        self.assertEqual(sess.userid, 123, "Assignment of uid  failed.")
        self.assertEqual(sess.created, current_stamp, "Assignment of created timestamp failed.")
        self.assertEqual(sess.last_seen, current_stamp, "Assignment of  access timestamp failed.")
        
        
    def test_15_internals(self):
        """HistoriaSession: __eq__ and __ne__"""

        # Two HistoriaRecords are equal when they have the same ID and same type.
        s1 = session.HistoriaSession(self.db)
        s2 = session.HistoriaSession(self.db)
        hr = core_data_objects.HistoriaRecord(self.db)

        self.assertNotEqual(s1, s2, "By default a blank record is equal to nothing else")
        self.assertNotEqual(s1, s1, "By default a blank record is equal to nothing else...even itself")
        
        s1.sessionid = "123"
        
        self.assertNotEqual(s1, s2, "Coming up as equal when they should have different IDs")
        
        s2.sessionid = "123"
    
        self.assertEqual(s1, s2, "With matched ID they report Not equal")
        self.assertNotEqual(hr, s2, "A generic is matching a setting")

    def test_20_new_id(self):
        """HistoriaSession: Generate a new session ID"""
        sess = session.HistoriaSession(self.db)
        
        session_id = sess.new_id()
        
        self.assertEqual(sess.sessionid, session_id, "New ID wasn't saved")
        
        
    def test_30_save(self):
        """HistoriaSession: save()"""
        sess = session.HistoriaSession(self.db)

        self.assertRaises(exceptions.DataConnectionError, sess.save)

        # Setup the database and try again.
        self.database_setup(withTables=True)
        
        self.assertRaises(exceptions.DataSaveError, sess.save)
        
        current_stamp = datetime.datetime.now()
        test_id = sess.new_id()
        sess.created = current_stamp
        sess.last_seen = current_stamp
        sess.ip = "127.0.0.1"
        sess.userid = 123
        self.assertTrue(sess._dirty, "Dirty bit not active but data changed")
        sess.save()
        
        self.assertFalse(sess._dirty, "Dirty bit active after save")
        
        # Now let's go see if it's really there
        select = ("SELECT * FROM `{0}`".format(session.HistoriaSession.machine_type),{})
        result = self.db.execute_select(select)
        
        self.assertEqual(len(result), 1, "There should be 1 and only 1 entry in the table.")
        self.assertEqual(result[0]['sessionid'], sess.sessionid, "sessionid in the table should match the sessionid on the record.")
        self.assertEqual(result[0]['userid'], sess.userid, "userid in the table should match the one on the record.")        
        self.assertEqual(result[0]['ip'], sess.ip, "ip in the table should match the one on the record.")        
        self.assertAlmostEqual(result[0]['created'], sess.created, delta=datetime.timedelta(seconds=1), msg="created in the table should match the one on the record.")        
        self.assertAlmostEqual(result[0]['last_seen'], sess.last_seen,  delta=datetime.timedelta(seconds=1), msg="last_seen in the table should match the one on the record.")        
        
    def test_33_save(self):
        """HistoriaSession: save() with only the minimum required settings"""
        sess = session.HistoriaSession(self.db)

        self.assertRaises(exceptions.DataConnectionError, sess.save)

        # Setup the database and try again.
        self.database_setup(withTables=True)

        self.assertRaises(exceptions.DataSaveError, sess.save)

        current_stamp = datetime.datetime.now()
        session_id = sess.new_id()
        sess.ip = "127.0.0.1"
        sess.userid = 123
        sess.save()

        self.assertFalse(sess._dirty, "Dirty bit active after save")

        # Now let's go see if it's really there
        select = ("SELECT * FROM `{0}`".format(session.HistoriaSession.machine_type),{})
        result = self.db.execute_select(select)

        self.assertEqual(len(result), 1, "There should be 1 and only 1 entry in the table.")
        self.assertEqual(result[0]['sessionid'], sess.sessionid, "sessionid in the table should match the sessionid on the record.")
        self.assertEqual(result[0]['ip'], sess.ip, "ip in the table should match the one on the record.")        
        self.assertEqual(result[0]['userid'], sess.userid, "userid in the table should match the one on the record.")
        
        # Resave and make sure we still only have one in the database (and force the update sql to run)
        sess.save()
        # Now let's go see if it's really there
        select = ("SELECT * FROM `{0}`".format(session.HistoriaSession.machine_type),{})
        result = self.db.execute_select(select)

        self.assertEqual(len(result), 1, "There should be 1 and only 1 entry in the table.")
        self.assertEqual(result[0]['sessionid'], sess.sessionid, "sessionid in the table should match the sessionid on the record.")
        self.assertEqual(result[0]['ip'], sess.ip, "ip in the table should match the one on the record.")        
        self.assertEqual(result[0]['userid'], sess.userid, "userid in the table should match the one on the record.")
        
        
    def test_40_load(self):
        """HistoriaSetting: load()"""
        self.database_setup(withTables=True)
        sess1 = session.HistoriaSession(self.db)
        current_stamp = datetime.datetime.now()
        session_id = sess1.new_id()
        sess1.ip = "127.0.0.1"
        sess1.userid = 123
        sess1.created = current_stamp
        sess1.last_seen = current_stamp
        sess1.save()

        sess2 = session.HistoriaSession(self.db)
        sess2.load(sess1.sessionid)

        self.assertEqual(sess1.sessionid, sess2.sessionid, "sessionid on original and loaded object don't match")
        self.assertFalse(sess2._dirty, "The dirty bit is wrong after load.")
        self.assertEqual(sess2, sess1, "The two copies of the record should consider themselves equal.")
        self.assertEqual(sess2.userid, sess1.userid, "userid in the table should match the userid on the record.")
        self.assertEqual(sess2.ip, sess1.ip, "ip in the table should match the one on the record.")
        self.assertAlmostEqual(sess2.created, sess1.created, delta=datetime.timedelta(seconds=1), msg="created in the table should match the one on the record.")        
        self.assertAlmostEqual(sess2.last_seen, sess1.last_seen,  delta=datetime.timedelta(seconds=1), msg="last_access in the table should match the one on the record.")        

        # Try to load with bogus ID
        self.assertRaises(exceptions.DataLoadError, sess2.load, '0215158c-93d9-2338-ac38-cb45e6096ed2') # that session id was generated during testing, so shouldn't come around again.
        

    def test_45_save_and_load(self):
        """HistoriaSetting: test save() then load() then save()."""
        self.database_setup(withTables=True)
        sess1 = session.HistoriaSession(self.db)
        current_stamp = datetime.datetime.now()
        session_id = sess1.new_id()
        sess1.ip = "127.0.0.1"
        sess1.userid = 123
        sess1.created = current_stamp
        sess1.last_seen = current_stamp
        sess1.save()

        sess2 = session.HistoriaSession(self.db)
        sess2.load(sess1.sessionid)
        
        sess2.save()
        
        
        # Now let's go see if it's really there
        select = ("SELECT * FROM `{0}`".format(session.HistoriaSession.machine_type),{})
        result = self.db.execute_select(select)
        
        self.assertEqual(sess1.sessionid, sess2.sessionid, "sessionid on original and loaded object don't match")
        self.assertEqual(len(result), 1, "There should be 1 and only 1 entry in the table.")
        self.assertEqual(result[0]['sessionid'], sess2.sessionid, "sessionid in the table should match the sessionid on the record.")
        self.assertEqual(result[0]['ip'], sess2.ip, "ip in the table should match the one on the record.")        
        self.assertEqual(result[0]['userid'], sess2.userid, "userid in the table should match the one on the record.")


    def test_50_delete(self):
        """HistoriaSetting: delete()"""
        self.database_setup(withTables=True)
        sess1 = session.HistoriaSession(self.db)
        current_stamp = datetime.datetime.now()
        session_id = sess1.new_id()
        sess1.ip = "127.0.0.1"
        sess1.userid = 123
        sess1.created = current_stamp
        sess1.last_seen = current_stamp
        sess1.save()

        sess1.delete()

        # Now let's go see if it's really there
        select = ("SELECT * FROM `{0}`".format(session.HistoriaSession.machine_type),{})
        result = self.db.execute_select(select)

        self.assertEqual(len(result), 0, "There should nothing in the table now.")
        self.assertEqual(-1, sess1.id, "The ID should reset to -1")
    
if __name__ == '__main__':
    unittest.main()