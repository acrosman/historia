"""
Internal Exceptions Module defines all exceptions that are raised by members of
the Internals package.
"""
#    This file is part of historia.
#
#    historia is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    historia is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with historia.  If not, see <http://www.gnu.org/licenses/>.


class HistoriaException(Exception):
    """Base exception class for all errors defined in this package."""
    pass



###############################################################################
##               Controller Exceptions
###############################################################################

class ControllerException(HistoriaException):
    """Base exception class for all errors raised by the Controller."""
    pass

class ControllerNotReady(ControllerException):
    """Raised when an attempt is made to use the controller and all the needed
    elements are not in place (like GUI and connection to the database)."""
    pass

class DatabaseNotReady(ControllerException):
    """Raised when an attempt is made to access the database but the database
    connection is not setup yet."""
    pass

class InterfaceNotReady(ControllerException):
    """Raised when an attempt is made to use the interface but the interface
    is not setup yet."""
    pass

class RecordNotFound(ControllerException):
    """Base class for errors raised when various records are not found during
    all types of searches (like calls to the find commands."""
    pass

class TypeMismatch(ControllerException):
    """Raised when an attempt is made to access an object of the wrong type."""
    pass

###############################################################################
##               Web Interface Exceptions
###############################################################################

class WebException(HistoriaException):
    """Base exception class for all errors raised by the Web interface."""
    pass

class HTTPException(WebException):
    """An exception that when raised should result in an provided HTTP error code."""
    def __init__(self, message, response_code=404):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        self.response_code = response_code
    
    def __str__(self):
        return "Response Code {0}: {1}".format(self.response_code, super().__str__())



