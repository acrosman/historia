#!/usr/bin/env python3
# encoding: utf-8
"""
This is the main historia launching script.  This will change dramatically
over time, right now it is just being used to setup aspects of the program
for later refinement, and to inspire testing setup.  Sins may be committed here
that are strictly forbidden elsewhere (like hard coding file names).

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

# Python Packages
import sys
import argparse
import pkgutil

# Historia Packages
from internals.controllers import *
from internals.web import *

__author__      = "Aaron Crosman"
__copyright__   = "Copyright 2015, Aaron Crosman"
__credits__     = ["Aaron Crosman"]
__license__     = "GPL"
__version__     = "0.0.1"
__maintainer__  = "Aaron Crosman"
__status__      = "Pre-Alpha"


def historia_version():
    """Print historia and python version information."""
    v_string = "{0} maintained by {1}. Status: {2} \n\n".format(__version__, __maintainer__, __status__)
    return v_string

parser = argparse.ArgumentParser(prog="Historia")
parser.add_argument('-c','--config', help="The path to the configuration files to load for historia. Historia will look for a default.json and a historia.json at the location; only default.json is required.")
parser.add_argument('-v','--version', help="Print the version information for Historia and the local Python installation.", action="version", version='%(prog)s: ' + historia_version())
parser.add_argument('--install', help="Install a fresh master database.  *Warning*: all data in the master will be lost! Make a backup if there is anything important in that database.", action="store_true")

args = parser.parse_args()

settingsLocation = '../config'

if args.config is not None:
    settingsLocation = args.config

master_controller = HistoriaCoreController(settingsLocation)

if args.install:
    settings = {
        "user": master_controller.config['database']['user'],
        "password": master_controller.config['database']["password"],
        "host": master_controller.config['database']['host'],
        "raise_on_warnings": False
    }

    master_controller.database = master_controller.create_database(database_name=master_controller.config['database']['main_database'],
                                                                    connection_settings=settings,
                                                                    db_type = "system")
    master_controller.logger.info("Master Database Created.")
    master_controller.user_create(session = None,
                                  parameters={'name':'admin',
                                         'email':'admin@example.com',
                                         'password': 'admin',
                                         'admin': 1,
                                         'enabled':1
                                         },
                                  bypass=True)

master_controller.setup_web_interface()
master_controller.start_interface()
