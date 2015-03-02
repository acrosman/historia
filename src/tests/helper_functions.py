#!/usr/bin/env python3
# encoding: utf-8
"""
helper_functions.py

Created by Aaron Crosman on 2015-02-22.

    This file is part of historia, and provides simple helpers used by the
    testing suite to load configuration and other repetative tasks.

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
import sys, os, os.path
import logging
import datetime
import json


def load_configuration(file_location):
    """Load the configuration files for Historia test suite. 
    Similar to the method of the same name on controller objects"""
    default_file =  os.path.join(file_location,"default.json")
    override_file =  os.path.join(file_location,"historia.json")
    override_status = {}
    
    with open(default_file, 'rt') as f:
        base_config = json.load(f)
    
    override_config = {}
    try:
        with open(override_file, 'rt') as f:
            override_config = json.load(f)
    except Exception as err:
        override_status = { # we'll log this failure later, but since it's a reasonable condition we continue
            'Success': False,
            'Message': "Failed to load configuration override file {0} due to {1}. This may be an expected result, conitnuing.".format(override_file, str(err))
        }
    else:
       override_status = {
             'Success': True,
             'Message': "Override file loaded from {0}".format(override_file)
       }
    
    config = deep_dict_merge(base_config, override_config)
    
    if config is None:
        raise Exception("Unable to load default.json configuration file in {0}. Resulting dictionary is empty".format(file_location))
    
    logging.config.dictConfig(config['logging'])
    
    test_logger = logging.getLogger("historia.test")
    
    if override_status['Success']:
        test_logger.info(override_status['Message'])
    else:
        test_logger.warn(override_status['Message'])
    
    return config


def deep_dict_merge(base_dict, update_dict):
    """Inplace deep merge update_dict into base_dict. Intended as a deep version of update()"""

    for key in update_dict:
        if key in base_dict:
            if isinstance(update_dict[key], dict) and isinstance(base_dict[key], dict):
                deep_dict_merge(base_dict[key], update_dict[key])
            else:
                base_dict[key] = update_dict[key]
        else:
            base_dict[key] = update_dict[key]

    return base_dict

