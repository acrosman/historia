#!/usr/local/bin/python3
# encoding: utf-8
"""
user_db.py

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

import sys
import os

from .core_data_objects import *
from .settings import *
from .exceptions import *


class HistoriaUserDatabase(HistoriaDatabase):
    type_label = "Historia User Database"
    machine_type = "historia_user_database"
    
    def __init__(self, database_name):
        super().__init__(database_name)
        
        self.member_classes = [
        
        ]
        

if __name__ == '__main__':
    import unittest
    
    import tests.test_user_db
    
    localtests = unittest.TestLoader().loadTestsFromModule(tests.test_user_db)
    unittest.TextTestRunner(verbosity=2).run(localtests)
