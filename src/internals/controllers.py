#!/usr/local/bin/python3
# encoding: utf-8
"""
contollers.py

This files is part of the internals package to handle controllers and other internal functions..


Created by Aaron Crosman on 2015-02-01

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
import datetime
import logging

from .exceptions import *

from database import system_db, user, session
from database import core_data_objects

from .web import *

class HistoriaCoreController(object):
    
    def __new__(cls, *args):
        """
        The __new__ override provides the logger object for all child data 
        objects in the system and forces a few shared assumptions about 
        attributes.
        """
        obj = super(HistoriaCoreController, cls).__new__(cls)
        obj.logger = logging.getLogger("historia.ctrl")
        
        return obj
    
    def __init__(self, database = None, interface = None):
        self.database = database
        self.interface = interface
        
        self.active_users = {}
        self.active_user_databases = {}
        
        self.routers = {
            'system': {
                'user_login'    : self.process_login,
                'end_session'   : self.end_session,
                'status'        : self.system_status
            },
            user.HistoriaUser.machine_type: {
                'create': user.HistoriaUser,
                'update': 'save',
                'delete': 'delete',
                'load'  : 'load'
            }
        }
        
        self.patterns = []
        self.request_patterns(reset=True)
        
        self.interface_settings = {
            'port': 8080
        }
    
    def setup_web_interface(self):
        self.interface = HistoriaServer()
    
    def start_interface(self):
        self.interface.startup(self)
    
    def process_request(self, request_handler, session_id, object, request, parameters):
        """Process requests from a request_handler and send back the results"""
        if object not in self.routers:
            request_handler.send_error(404, "Requested Resource not found")
            return
            
        if session_id is None:
            request_handler.send_home()
            return
            
        
        
    
    def process_login(self, parameters):
        return self.authorize_user(paramters['user'], parameters['password'])
            
    def system_status(self):
        pass
    
    def request_patterns(self, reset=True):
        """Return a list with all valid URL patterns for the web interface."""
        
        if reset:
            self.patterns = []
        
            for route in self.routers:
                for command in self.routers[route]:
                    self.patterns.append(route + "/" + command)
        
        return self.patterns
        
        
    #====================================
    def create_database(self, database_name, connection_settings, db_type = "user"):
        """Create a new database with database_name. The optional parameter allows the caller to pick the type of database to be created.  Valid types are: system or user."""
        
        if db_type == 'system':
            db = system_db.HistoriaSystemDatabase(database_name)
            db.connection_settings = connection_settings
            db.createDatabase(db)
            return db
        elif db_type == 'user':
            raise NotImplemented('User Databases have not been implemented yet')
        else:
            raise ValueError("Databases much be of type 'system' or 'user'")
    
    def load_database(self, database_name):
        """Setup a connection to an existing database based on database name."""
        pass
    
    def authenticate_user(self, user_name, password):
        """Check the user_name and password. If it is a validate user, return a user object."""
        if self.database is None:
            raise ControllerNotReady("The controller is not fully configured, not database object.")
        
        if not self.database.connected:
            self.database.connect()
            if not self.database.connected:
                raise DatabaseNotReady('Cannot connect to database')
        
        search = core_data_objects.HistoriaDatabaseSearch(self.database, user.HistoriaUser.machine_type)
        
        search.add_field('id')
        search.add_condition('name', user_name)
        search.add_condition('email', user_name, '=', 'OR')
        search.add_limit(1)
        test_user = user.HistoriaUser(self.database)
        try:
            results = search.execute_search()
            test_user.load(results[0]['id'])
            if(test_user.checkPassword(password)):
                return test_user
            else:
                return False
        except:
            return False
        
    
    def check_access(self, user, database):
        """Check that a user has access to a given database. Both parameters can be either the name or the object representation."""
        pass
    
    def start_session(self, ip):
        """Return a new session object"""
        sess = session.HistoriaSession()
        sess_id = sess.new_id()
        sess.ip = ip
        sess.userid = 0
        sess.save()
        
        self.logger.info("New session started with ID: {0}".format(sess_id))
        
        return sess
        
    
    def validate_session(self, session_id):
        """Make sure the provided session is valid"""
        pass
        
    def end_session(self, session_id):
        """End a given user's session, and close their database connection to free resources."""
        pass
