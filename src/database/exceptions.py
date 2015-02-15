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

###############################################################################
##                Exceptions
###############################################################################

class HistoriaDataException(Exception):
    """Base exception class for all errors defined in this package."""
    pass

class DataConnectionError(HistoriaDataException):
    """Raised when the database connection cannot be established."""
    pass

class DatabaseCreationError(HistoriaDataException):
    """Raised when there is a failed attempt to create a new database."""
    pass

class DatabaseCheckError(HistoriaDataException):
    """Raised by the Database class checkDatabase method."""
    def __init__(self, flags = {}):
        """Each table in the database has a flag that can be set when the error
        is raised to indicate which tables are in working order."""
        self.flags = flags

class DataLoadError(HistoriaDataException):
    """Raised when there is a problem loading data from the database. Generally 
    this means something related to errors in the structure or connection.
    Failed searches and invalid IDs raise a different error."""
    pass

class DataSaveError(HistoriaDataException):
    """Raised when there is a problem saving data to the database. Generally 
    this means something related to errors in the structure or connection.
    Failed searches and invalid IDs raise a different error."""
    pass

class NoSuchRecord(HistoriaDataException):
    """Raised when a data object attempts to load or update itself and discovers
    that it has an invalid ID."""
    pass

class SearchError(HistoriaDataException):
    """Raised when a search fails due to an error in the search object, and there are no matching objects."""
    pass


class NoSearchResults(SearchError):
    """Raised when a search is performed, and there are no matching objects."""
    pass

class InvalidDataError(HistoriaDataException):
    """Raised when an attempt to save invalid data is made."""
    pass

class SourceTypeError(HistoriaDataException):
    """Raised when there is a problem with a SourceType object."""
    pass
