#!/usr/local/bin/python3
# encoding: utf-8
"""
core_data_objects.py

This files is part of the DAL package to handle basic HistoriaRecord interactions.

All other parts of the DAL are derived from this class.


Created by Aaron Crosman on 2015-01-20.

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
import logging
import datetime
import json, string

import mysql.connector

from .exceptions import *


class HistoriaDataObject(object):
    
    type_label = "HistoriaDataObject"
    machine_type = "HistoriaDataObject"
    
    def __new__(cls, *args):
        """
        The __new__ override provides the logger object for all child data 
        objects in the system and forces a few shared assumptions about 
        attributes.
        """
        obj = super(HistoriaDataObject, cls).__new__(cls)
        obj._logger = logging.getLogger("historia.db")
        obj._id = -1
        
        return obj
        
    @property
    def id(self):
        return self._id


class HistoriaDatabase(HistoriaDataObject):
    
    type_label = "Historia Database"
    machine_type = "historia_database"
    
    def __init__(self, database_name):
        self.name = database_name
        self._id = None
        self.connection_settings = {
          'user': '',
          'password': '',
          'host': '127.0.0.1',
          'database': self.name,
          'raise_on_warnings': False
        }
        self.member_classes = []
        self.database_defaults = {
            'charset': 'utf8'
        }
        self.connection = None
    
    def __setattr__(self, name, value):
        # Don't allow a database name that would be invalide to MySQL
        if name == 'name' and value is not None:
            value = value.lower()
            chars = set(string.ascii_letters + string.digits + '_')
            if not all((c in chars) for c in value):
                raise ValueError("Cannot set database name to {0}".format(value))
        
        HistoriaDataObject.__setattr__(self, name, value)
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(**self.connection_settings)
            return True
        except mysql.connector.Error as err:
             self._logger.error("Unable to establish database connection: {0}".format(str(err)))
             raise DataConnectionError("Unable to establish database connection: {0}".format(str(err)))

    def disconnect(self):
        if self.connected:
            self.connection.close()
            return True

    def commit(self):
        if self.connected:
            self.connection.commit()
            return True
        
    def cursor(self):
        """Return a cursor connected to this record's database."""
        try:
            if not self.connected:
                raise DataConnectionError('Cannot save record when there is no active data connection')
        except AttributeError as err:
            raise DataConnectionError('Invalid database object, cannot connect to database.')
        
        return self.connection.cursor(dictionary=True)
    
    @property
    def connected(self):
        if self.connection == None:
            return False
        
        return self.connection.is_connected()
    
    def generate_database_SQL(self):
        """Generate the SQL statements to create the empty database.
        It cannot be assumed that the connection defined for this database has
        the access to actually create a new one. This just generates the SQL
        statements to be executed else where by a user with access.
        
        @returns: an tuple of statements to execute."""
        
        statements = []
        
        # Base statements to create a database
        sql = "CREATE DATABASE IF NOT EXISTS `{0}` DEFAULT CHARACTER SET {1}".format(self.name, self.database_defaults['charset'])
        params = {}
        statements.append( (sql, params) )
        
        # Add Use database statement to the process
        sql = "USE `{0}`".format(self.name)
        statements.append( (sql, params) )
        
        # Create statements for each MemberClass's table
        for member in self.member_classes:
            statements += member.generate_SQL()
        
        return tuple(statements)
    
    # ================= Database Helpers ================
    def execute_insert(self, prepared_statement):
        
        if not self.connected:
            raise DataConnectionError("Cannot insert into database, no active connection")
        
        try:
            cur = self.cursor()
            cur.execute(prepared_statement[0], prepared_statement[1])
            self.commit()
            newId = cur.lastrowid
            cur.close()
            self._logger.debug("Inserted Data: {0}, values {1}".format(*prepared_statement))
            return newId
        except mysql.connector.Error as err:
            raise DataSaveError("Unable to add record to database: {0}, values {1}".format(*prepared_statement))


    def execute_select(self, prepared_statement):

        if not self.connected:
            raise DataConnectionError("Cannot insert into database, no active connection")
        

        try:
            cur = self.cursor()
            cur.execute(prepared_statement[0], prepared_statement[1])
            result = cur.fetchall()
            self._logger.debug("Selected Data: {0}, values {1}".format(*prepared_statement))
            cur.close()
            return result
        except mysql.connector.Error as err:
            self._logger.error('Unable to execute SQL statement {0}, values {1}'.format(*prepared_statement))
            raise DataLoadError("Unable to load data from database.{0}, values {1}".format(*prepared_statement))

    def execute_update(self, prepared_statement):

        if not self.connected:
            raise DataConnectionError("Cannot insert into database, no active connection")
        
        try:
            cur = self.cursor()
            cur.execute(prepared_statement[0], prepared_statement[1])
            self.commit()
            rows = cur.rowcount
            self._logger.debug("Updated {0} rows using: {1}, values {2}".format(rows,*prepared_statement))
            cur.close()
            return rows
        except mysql.connector.Error as err:
            self._logger.error('Unable to execute SQL statement {0}, values {1}'.format(*prepared_statement))
            raise DataSaveError("Unable to load data from database.{0}, values {1}".format(*prepared_statement))


        
class HistoriaRecord(HistoriaDataObject):
    
    type_label        = "Historia Generic Record"
    machine_type      = "historia_generic"
    _table_settings    = { 'ENGINE': 'InnoDB',
                          'DEFAULT CHARSET': 'utf8'
                        }
    _table_fields      = {'id': {
                                    'type':       'int',
                                    'length':     '11',
                                    'signed':     False,
                                    'allow_null': False,
                                    'default':    'AUTO_INCREMENT',
                                    'index':      { 'type':'PRIMARY', 'fields': ('id',)},
                                    'order':    0
                                },
                            'value': {
                                    'type':       'char',
                                    'length': '5',
                                    'default': 'NULL',
                                    'allow_null': True,
                                    'order': 1
                                }
                                
                            }
    
    # Fields are defined as follows (this should get documented someplace better)
    # _table_fields = {'field_name': {'type': [type_name], 
    #                                'length': [as_needed_by_type], 
    #                                'signed': [TRUE/FALSE]
    #                                'allow_null': [TRUE/FALSE],
    #                                'default': [default value when needed or AUTO_INCREMENT],
    #                                'update_timestamp': [TRUE/FALSE on timestamp field only],
    #                                'index' : {'type' : [PRIMARY/UNIQUE/BASIC], 
    #                                           'name' : [Optional name],
    #                                           'fields': [List, of, fields]},
    #                                'order' : [order it should be added to the table]
    #                }}
    
    def __init__(self, database):
        
        # Assign all the attributes for the class list of fields
        for field in type(self)._table_fields:
            if field is not 'id':
                setattr(self, field, None)
        
        self.database = database # Links back to the database that owns this record
        self._dirty = False # Updated whenever there are unsaved changes around, but we're clean by definition when created
        
    
    def __setattr__(self, name, value):
        """
        Use __setattr__ to detect changes to the object so that we can check
        the field list for value attributes and to set the dirty bit to see
        if a save is required. 
        
        Subclasses that wish to filter attributes in ways beyond this function
        should raise any needed exceptions, call this function, and handle any
        exceptions raised here.
        """
        
        if name[:1] is not "_" and name is not 'database' and name not in type(self)._table_fields:
            raise AttributeError('Cannot set attribute {0} because there is no matching field on this record type'.format(name))
        
        # Check the type on things to be mapped to SQL fields. None is allows permitted through.
        if name in type(self)._table_fields and value is not None:
            attr_type = type(self)._table_fields[name]['type']
            if self._is_type_int(attr_type) and not isinstance(value, int):
                raise ValueError("{0} should be an int but {1} provided".format(name, type(value)))
            elif self._is_type_text(attr_type) and not isinstance(value, str):
                raise ValueError("{0} should be a text type (str) but {1} provided".format(name, type(value)))
            elif self._is_type_float(attr_type) and not isinstance(value, float):
                raise ValueError("{0} should be a float type  but {1} provided".format(name, type(value)))
            elif self._is_type_datetime(attr_type) and not isinstance(value, datetime.datetime):
                raise ValueError("{0} should be a datetime type but {1} provided".format(name, type(value)))
        
        HistoriaDataObject.__setattr__(self, name, value)
        if name != '_dirty':
            HistoriaDataObject.__setattr__(self, '_dirty', True)
    
    def __eq__(self, other):
        if self.id == -1:
            return False
        else:
            try:
                if self.machine_type == other.machine_type:
                    return self.id == other.id
                else:
                    return False
            except AttritbuteError:
                return False
            
    def __ne__(self, other):
        if self.id == -1:
            return True
        else:
            try: 
                if self.machine_type == other.machine_type:
                    return self.id != other.id
                else:
                    return True
            except AttritbuteError:
                return True
    
    def to_JSON(self):
        """Return a JSON encoded string representing this object."""
        
        json_string = ''
        
        for field in type(self)._table_fields:
            value = getattr(self, field)
            if value is not None:
                if self._is_type_datetime(type(self)._table_fields[field]['type']):
                    json_string = '{0}\n"{1}":{2},'.format(json_string, field, json.dumps(value.strftime('%Y-%M-%d %H:%M:%S')))
                else:
                    json_string = '{0}\n"{1}":{2},'.format(json_string, field, json.dumps(value))
        json_string = '{{0}}'.format(json_string[:-1])
        
        return json_string
    
    # ============== CRUD methods ==================
    def save(self):
        """Save this record to the database."""
        
        if self.id == -1:
            self._id = self.database.execute_insert(self._generate_insert_SQL())
        else:
            self.database.execute_update(self._generate_update_SQL())
        self._dirty = False

    def delete(self):
        """Save this record to the database."""

        if self.id != -1:
            self.database.execute_update(self._generate_delete_SQL())
            self._id = -1
    
    def load(self, recordID):
        """Load a record from the database into this object."""
        
        if self.id != -1:
            raise DataLoadError("Cannot load a record into a record object already in new.  Memory is cheap, create a new one.")
        
        data = self.database.execute_select(self._generate_select_SQL(recordID))
        
        if len(data) < 1:
            raise DataLoadError("No records found with matching ID {0}".format(recordID))
        
        if len(data) > 1:
            self.logger.error("Duplicate records found with matching ID{0}".format(recordID))
            raise DataLoadError("Duplicate records found with matching ID{0}".format(recordID))
        
        data = data[0]
        
        for field in data:
            if field == 'id':
                self._id = data[field]
            else:
                setattr(self, field, data[field])
        
        self._dirty = False
        
    # ============== Database Generation Methods ==================
    @classmethod
    def generate_SQL(cls):
        """Generate the SQL statements to create the class table(s) and idexes
        This just generates the SQL statements to be executed in a context 
        able to run the included queries.
        
        @returns: an tuple of statements to execute."""
        
        statements = []
        
        # Drop table as needed
        sql = "DROP TABLE IF EXISTS `{0}`".format(cls.machine_type)
        params = {}
        statements.append( (sql, params) )
        
        # Start the create table statement
        sql = "CREATE TABLE IF NOT EXISTS `{0}` (".format(cls.machine_type)
        indexes = []
        # Create statements for each MemberClass's table
        fields = [[cls._table_fields[k]['order'],k] for k in cls._table_fields ]
        for field in sorted(fields):
            sql += cls._generate_field_SQL(field[1], cls._table_fields[field[1]])
            if 'index' in cls._table_fields[field[1]]:
                indexes.append( cls._table_fields[field[1]]['index'] ) # save these for later
        
        # Now add the indexes
        for idx in indexes:
            sql += cls._generate_index_SQL(idx)
        sql = sql[:-2]+"\n" # crop the extra ,
        
        # Close the create table statement
        sql += ")"
        for setting, value in cls._table_settings.items():
            sql += " {0} = {1} ".format(setting, value)
        sql += ';'
        
        statements.append( (sql, params) )
        
        return tuple(statements)
    
    @staticmethod
    def _generate_field_SQL(field_name, settings ):
        # Field settings are defined as follows (this should get documented someplace better)
        #   {'type': [type_name], 
        #    'length': [as_needed_by_type],
        #    'signed': [TRUE/FALSE as needed by type] 
        #    'allow_null': [TRUE/FALSE],
        #    'default': [default value can be MySQL constant and must include any needed ' marks],
        #    'update_timestamp': [TRUE/FALSE on timestamp field only]
        #    'index' : {INDEX DEFININTION}
        #   }
        
        line = "`{0}` {1}".format(field_name, settings['type'])
        
        if 'length' in settings:
            line += "({0}) ".format(settings['length'])
        
        if 'signed' in settings:
            if not settings['signed']:
                line += ' unsigned '
                
        if not settings['allow_null']:
            line += ' NOT NULL '
        
        if 'default' in settings and settings['default'] is not None:
            if settings['type'] == 'datetime' and settings['default'] == 'NOW()':
                line += " DEFAULT NOW() "
            elif settings['type'] == 'timestamp' and settings['default'] == 'CURRENT_TIMESTAMP':
                line += " DEFAULT CURRENT_TIMESTAMP "
            elif settings['default'] is None:
                pass
            elif settings['default'] == 'AUTO_INCREMENT':
                line += ' AUTO_INCREMENT '
            else:
                line += " DEFAULT '{0}' ".format(settings['default'])
        
        if 'update_timestamp' in settings:
            if settings['update_timestamp']:
                 line += " ON UPDATE CURRENT_TIMESTAMP "
        
        return line + ',\n'
    
    @staticmethod
    def _generate_index_SQL(index):
        # Indexes are defined as follows.
        #    'index' : {'type' : [PRIMARY/UNIQUE/BASIC], 
        #               'name' : [Optional name],
        #               'fields': [List, of, fields]
        #               }
        line = ''
        if index['type'] != 'BASIC':
            line += index['type']
        
        line += " KEY "
        
        if 'name' in index:
            line += "`%s` "%index('name')
        
        line += "("
        for f in index['fields']:
            line += "`%s`, "%f
        line = line[:-2] + "),\n"
        
        return line
    
    #  =============== CRUD Helpers ===================
    def _generate_insert_SQL(self):
        #INSERT INTO `Users` (`id`, `name`, `email`, `pass`, `modified`, `created`, `last_access`, `enabled`, `admin`) VALUES (NULL, 'aaron', 'acrosman@gmail.com', 'bcrypt_hash', CURRENT_TIMESTAMP, NOW(), NULL, '1', '0');
        
        fields = {}
        
        statement = "INSERT INTO `{0}` ( ".format(self.machine_type)
        value_placeholders = ""
        for field in self._table_fields:
            # A little error checking and cleanup to make sure there is a default
            if 'default' not in self._table_fields[field]:
                self._table_fields[field]['default'] = None
            if not self._table_fields[field]['allow_null'] and getattr(self, field) == None and self._table_fields[field]['default'] == None:
                raise DataSaveError("{0} cannot be Null".format(field))
            if self._table_fields[field]['type'] == 'timestamp':
                continue # timestamps should be set to care for themselves.
            if self._table_fields[field]['default'] =='AUTO_INCREMENT':
                fields[field] = None
            elif self._table_fields[field]['type'] == 'datetime' and not self._table_fields[field]['allow_null'] and getattr(self, field) == None:
                statement += "`{0}`,".format(field)
                value_placeholders += "NOW(),"
            else:
                fields[field] = getattr(self, field)
                if fields[field] == None and self._table_fields[field]['default'] != None:
                    fields[field] =self._table_fields[field]['default']
                statement += "`{0}`,".format(field)
                value_placeholders += "%({0})s,".format(field)
        
        statement = statement[:-1] + " ) VALUES ( " + value_placeholders[:-1] + ")"
        
        return (statement, fields)
    
    def _generate_select_SQL(self, primary_id):
        
        fields = {}
        statement = "SELECT * FROM `{0}` ".format(self.machine_type)
        
        for field in self._table_fields:
            if 'index' in self._table_fields[field]:
                if self._table_fields[field]['index']['type'] == 'PRIMARY':
                    statement += "WHERE `{0}` = %({1})s".format(field,field)
                    fields[field] = primary_id
        
        return (statement, fields)
        
    
    def _generate_update_SQL(self):
        
        fields = {}
        primary = ''
        
        statement = "UPDATE `{0}` SET ".format(self.machine_type)
        
        for field in self._table_fields:
            if 'default' not in self._table_fields[field]:
                self._table_fields[field]['default'] = None

            if 'index' in self._table_fields[field]:
                if self._table_fields[field]['index']['type'] == 'PRIMARY':
                    primary = field
                
            if self._table_fields[field]['default'] =='AUTO_INCREMENT':
                continue # Don't touch auto fields
            
            if self._table_fields[field]['type'] == 'timestamp':
                continue # timestamps should be set to care for themselves.

            fields[field] = getattr(self, field)
            statement += "`{0}` = %({1})s,".format(field, field)
        
        
        statement = statement[:-1] + " WHERE `{0}` = %({1})s".format(primary, primary)
        fields[primary] = getattr(self, primary)
        
        return (statement, fields)
    
    def _generate_delete_SQL(self):
        
        statement = "DELETE FROM `{0}` ".format(self.machine_type)
        fields = {}
        for field in self._table_fields:
            if 'index' in self._table_fields[field]:
                if self._table_fields[field]['index']['type'] == 'PRIMARY':
                    statement += " WHERE `{0}` = %({1})s".format(field, field)
                    fields[field] = getattr(self, field)
        
        return (statement, fields)
        
    #================ Other Helpers =====================
    @staticmethod
    def _is_type_text(field_type):
        """Helper function to determine if a given field type is a type that can be made a python str."""
        field_type = field_type.lower()
        if field_type == 'varchar':
            return True
        if field_type == 'char':
            return True
        if field_type == 'text':
            return True
        if field_type == "longtext":
            return True
        if field_type == "mediumtext":
            return True
        if field_type == 'tinytext':
            return True

        return False 

    @staticmethod
    def _is_type_int(field_type):
        """Helper function to determine if a given field type is a type that can be made a python int."""
        field_type = field_type.lower()
        if field_type == 'int':
            return True
        if field_type == 'smallint':
            return True
        if field_type == 'mediumint':
            return True
        if field_type == 'integer':
            return True
        if field_type == 'bigint':
            return True
        if field_type == 'tinyint':
            return True
        return False
        
    @staticmethod
    def _is_type_float(field_type):
        """Helper function to determine if a given field type is a type that can be made a python float."""
        field_type = field_type.lower()
        if field_type == 'double':
            return True
        if field_type == 'float':
            return True
        if field_type == 'double presicion':
            return True
        if field_type == 'real decimal':
            return True
        if field_type == 'numeric':
            return True
        return False

    @staticmethod
    def _is_type_datetime(field_type):
        """Helper function to determine if a given field type is a type that can be made a python datetime."""
        field_type = field_type.lower()
        if field_type == 'date':
            return True
        if field_type == 'datetime':
            return True
        if field_type == 'timestamp':
            return True
        if field_type == 'time':
            return True
        if field_type == 'year':
            return True
        return False
    
    
class HistoriaDatabaseSearch(object):
    """HistoriaDatabaseSearch: And object for searching historia databases. 
    This class provides all search queries. If you aren't using this call
    and you're not a test case, you are probably doing it wrong. If this
    class can't do what you need, fix this class."""
    
    def __init__(self, database, search_scope=None):
        """Database searches are limited to one database. If no search_scope
        type is provided it is assumed all object types in that database
        should be searched. search_scope type can be a class reference or list
        of class references."""
        
        self.database = database
        self.search_scope = search_scope
        self._return_fields = {}
        self._joins = {} # indexed by joined table
        self._conditions = []
        self._sorts = []
        self._limit = None
        self.saved_results = None
        
        
    def add_field(self, field_name, alias=None):
        if alias is None:
            alias = field_name
        self._return_fields[field_name] = alias
    
    def add_expression(self, expression, values={}, alias=None):
        if alias is None:
            alias = "expression_{0}".format(len(self._return_fields))
        self._return_fields[alias] = (expression, values, alias)
    
    def add_join(self, main_field, table, table_field, operation = "="):
        self._joins[table] = (main_field, table_field, operation)
    
    def add_condition(self, field, value, comparison = "=", scope="AND"):
        if scope is not "AND" and scope is not "OR":
            raise ValueError("Scope must be AND or OR")
        self._conditions.append((field, value, comparison, scope))
    
    def add_sort(self, field, direction="ASC"):
        if direction is not "ASC" and direction is not "DESC":
            raise ValueError("Sort direction must be 'ASC' or 'DESC'")
        self._sorts.append((field, direction))
    
    def add_limit(self, limit=None):
        self._limit = limit
    
    def _generate_sql(self):
        """Returns (select_statement, values)"""
        
        sql = "SELECT "
        values = {}
        for f in self._return_fields:
            if isinstance(self._return_fields[f], tuple):
                t = self._return_fields[f]
                sql += " {0} AS {1},".format(t[0], t[2])
                for v in t[1]: # this contains the values from the add_expression method
                    values[v] = v
            else:
                sql += " `{0}` AS {1},".format(f, self._return_fields[f])
        
        sql = sql[:-1] + ' FROM `{0}` '.format(self.search_scope)
        
        for j in self._joins:
            sql += " LEFT JOIN {0} ON {1} {2} {3} ".format(j, self._joins[j][0], self._joins[j][2], self._joins[j][1])
        
        sql += " WHERE "
        first = True
        for c in self._conditions:
            if not first:
                sql += c[3]
            
            # Make sure we have a unquie index for the values
            inc = 0
            base = c[0]
            index = base
            while index in values:
                index = "{0}_{1}".format(base, inc)
                inc += 1
                
            place_holder = '%({0})s'.format(index)
            
            sql += " `{0}` {1} {2} ".format(c[0], c[2], place_holder)
            values[index] = c[1]
            first = False
        
        if len(self._sorts) > 0:
            sql += " ORDER BY "
            for s in self._sorts:
                sql += " `{0}` {1}".format(s[0], s[1])
        
        if self._limit is not None:
            sql += " LIMIT {0}".format(self._limit)
        
        return (sql, values)
        
    def execute_search(self):
        if self.search_scope is None:
            raise SearchError("Seach scope not set")
        statement = self._generate_sql()
        results = self.database.execute_select(statement)
        if len(results) is 0:
            raise NoSearchResults("No search results found")
        else:
            self.saved_results = results
        return self.saved_results
        
if __name__ == '__main__':
    import unittest
    import tests.test_core_data
    
    localtests = unittest.TestLoader().loadTestsFromModule(tests.test_core_data)
    unittest.TextTestRunner(verbosity=2).run(localtests)
