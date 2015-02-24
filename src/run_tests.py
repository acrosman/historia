#!/usr/bin/env python3
# encoding: utf-8
"""
run_tests.py 

Run a selected set of tests, either by providing a parameter or the script will ask.

Created by Aaron Crosman on 2015-01-28.

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
import argparse
import sys
import pkgutil
import warnings
import unittest


from tests import *


def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

parser = argparse.ArgumentParser()
parser.add_argument('-t','--test_group', help="The group of tests to run or 'all' for all tests")
parser.add_argument('-v','--verbosity', help="The verbosity level for the test runner", type=int, choices=[0,1,2])
parser.add_argument('-w','--warnings', help="If set, display runtime warnings.", action="store_true")


args = parser.parse_args()

if args.warnings:
    warnings.simplefilter('default')
    
test_groups = { 'all':          None, 
                'core_data':    test_core_data, 
                'systemdb':     test_system_db, 
                'userdb':       test_user_db, 
                'setting_obj':  test_settings_obj, 
                'user':         test_user, 
                'controller':   test_controllers, 
                'session':      test_session
              }

group_selected = None

if args.test_group is None:
    group_options = "Select a set of tests to run:\n"
    for k in test_groups.keys():
        group_options += "{0}\n".format(k)
    
    group_options += "q to quit\n--> "
    tests = ""
    while tests == "":
        tests = input(group_options)
        if tests not in test_groups:
            if tests == 'q':
                exit()
            tests = ""
            print("Invalid selection")
    
    group_selected = tests
elif args.test_group in test_groups:
    group_selected = args.test_group
else:
    print("Invalid test group: {0}. Options: {1}".format(args.test_group, test_groups))
    exit()

if args.verbosity is None:
    verbosity = 1
else:
    verbosity = args.verbosity

print_err("Running test group {0} at verbosity {1}".format(group_selected, verbosity))

test_suites = {}
test_results = []
if group_selected == "all":
    for group in test_groups:
        if group != 'all':
            test_suites[group] = unittest.TestLoader().loadTestsFromModule(test_groups[group])
else:
    test_suites[group_selected] = unittest.TestLoader().loadTestsFromModule(test_groups[group_selected])


verbose_start_header = """
===========================================================
==================== Starting Tests =======================
===========================================================
"""

short_start_header = "Starting Tests"

verbose_test_header = """
===========================================================
====================  {0} Tests =======================
===========================================================
"""

short_test_header = """{0} Tests"""

if verbosity == 2:
    print_err(verbose_start_header)
    test_header = verbose_test_header
else:
    print_err(short_start_header)
    test_header = short_test_header
    

for suite in test_suites:
    print_err(test_header.format(suite))
    test_results.append(unittest.TextTestRunner(verbosity=verbosity).run(test_suites[suite]))


print("\n===========================================================")
print(" ** Tests Complete** ")


total = sum([t.testsRun for t in test_results])
errors = sum([len(t.errors) for t in test_results])
failures = sum([len(t.failures) for t in test_results])
problems = errors + failures
percentage = ((total-problems)/total)


if problems > 0:
    print(problems,"problems found in {0}.  Please review the previous messages for details.".format(group_selected))
else:
    print("All tests passed!")

print("===========  Summary  =============")
print(total, "tests run")
print(errors, "errors")
print(failures, "failures")
print(problems, "total problems")
print("{:.2%} tests passed".format(percentage))

