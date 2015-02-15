'''
Created on Feb 5, 2015

@author: Aaron Crosman


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
'''

import urllib.parse
import threading
import os, os.path
import ssl
import http.server, http.cookies
from cgi import parse_header, parse_multipart

from .exceptions import *
from .controllers import *

class HistoriaServer(object):
    
    running = False
    
    def startup(self, controller, configLoc = None):
        '''Sets everything up'''
        
        # Set up the main Historia controller:
        self.controller = controller
        
        # Server List
        # self.Servers = []
        # self.ServerCount = 5
        
        # Get the port number from the controller's settings.
        port = self.controller.interface_settings['port']
        
        
        HistoriaHTTPHandler.setcontroller(self.controller)
                
        self.server = http.server.HTTPServer(('', int(port)), HistoriaHTTPHandler)
        print("HTTP Server starting up on port: {0}".format(port))
        
        # self.server_thread = threading.Thread(target=self.server.serve_forever)
        # self.server_thread.setDaemon(True)
        # self.server_thread.start()
        
        print("HTTP Server running on port: {0}".format(port))
        self.running = True
        self.server.serve_forever()
        
        
    def status(self, humanReadable = False):
      """Return the status of the server as a string"""
      
      if humanReadable:      
        if self.running:
          return "Server is running on port: %s" %self.controller.ServerSettings['port']
        else:
          return "Server offline"
      else:
        return self.running
      
    # Stop the web server. Should be called by controller or Handler.
    def stop(self):
        
        self.running = False
        self.server.shutdown()
        print ("Server Shutdown Complete")
        

class HistoriaHTTPHandler(http.server.BaseHTTPRequestHandler):
    
    # Standard Historia logging:
    logger = None
        
    # Path Namespace
    url_namespace = "historia"
    
    # Content-Type header options
    file_types = {
        'html': "text/html; charset=utf-8",
        'json': "application/json; charset=utf-8",
        'js': 'text/javascript',
        'css': 'text/css',
        'jpg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'default': 'text/plain'
    }
    
    # Historia Data controller to be used by all server threads
    controller = None
    
    # A list of valid URL patterns.
    patterns = []
    special_cases = ['files']
    
    # Location of files directory
    file_base_path =  os.path.join(os.getcwd(),"templates")
    
    def log_error(self, format, *args):
        if HistoriaHTTPHandler.logger == None:
            return
        else:
            HistoriaHTTPHandler.logger.error("HTTP Interface(%s): %s" %
                                         (self.address_string(),
                                         format%args))
    
    def log_message(self, format, *args):
        if HistoriaHTTPHandler.logger == None:
            return
        else:
            HistoriaHTTPHandler.logger.info("HTTP Interface(%s): %s" %
                                         (self.address_string(),
                                         format%args))
        
    @classmethod
    def setcontroller(cls, controller):
        cls.controller = controller
        cls.logger = controller.logger
        cls.patterns = controller.request_patterns()
    
    def _send_headers(self, code, contentType):
        """Setup and send the headers for a valid 200 text response"""
        self.send_response(code)
        self.send_header("content-type", contentType)
        self.end_headers()
    
    def send_record(self, record):
        pass
    
    def send_file(self, file_path):
        """Send a file. Path must be within file_base_path. If file_base_path is empty a 403 will always be raised."""
        if HistoriaHTTPHandler.file_base_path == "":
            self.send_error(403, "File base path not configured, all files blocked.")
        
        real_path = self._check_file(file_path)
        
        if not real_path:
            self.send_error(404, "{0} not found".format(file_path))
        
        extension = os.path.splitext(real_path)[-1].lower()[1:]
        content_type = HistoriaHTTPHandler.file_types[extension]
        try:
            
            mode = "r"
            if not content_type.startswith("text"):
                f = open(real_path, 'rb')
                self._send_headers(200, content_type)
                self.wfile.write(f.read())
            else:
                f = open(real_path, 'r')
                self._send_headers(200, content_type)
                self.wfile.write(f.read().encode('utf-8'))
                
                
            f.close()
        except IOError as err:
            self.send_error(404, "File Not Available: {0}".format(file_path))
        
        
    
    def _check_file(self, path):
        """Check to see if the provided filepath is within the ServerTemplates
        directory for Historia."""

        cleanpath = os.path.normpath(path)
        mypath = os.getcwd()

        # make sure they requested path does not include anything to move to 
        # a higher level directory.
        if mypath != os.path.commonprefix([mypath, os.path.join(mypath, cleanpath)]):
            return False

        # Now look to see if the path exists where it should. Search the list
        # of template directories.
        testpath = os.path.join(HistoriaHTTPHandler.file_base_path, cleanpath)
        if os.path.isfile(testpath):
            return testpath

        return False

    
    def do_GET(self):
        """ Handle get requests. """
        
        self.log_message("Processing GET request %s", self.path)
        
        # Split the query string from the path
        full_request = self.path.split('?')
        try:
            path_request = HistoriaHTTPHandler.ValidateURL(self.path)
        except HTTPException as err:
            self.send_error(err.response_code, str(err))
            return
        
        # Send the welcome page
        if path_request[0] == 'home':
            self.send_file('html/page.html')
        elif path_request[0] == 'files':
            self.send_file(path_request[1]) # File security handled by the send_file function
        # For all other values we send the request to the controller for handling.
        else:
            query_parameters = urllib.parse.parse_qs(full_request[1]) if len(full_request) == 2 else {}
            self.controller.process_request(None, path_request[0], path_request[1], query_parameters)
            

    def do_POST(self):
        """Handle post functions. """
        

        self.log_message("Processing POST request %s", self.path)
        
        try:
            path_request = HistoriaHTTPHandler.ValidateURL(self.path)
        except HTTPException as err:
            self.send_error(err.response_code, str(err))
            return
        
        try: 
            post_parameters = self.parse_POST()
        except Exception as err:
            self.log_error("Unhandled error processing posted data sent to {0}: {1}".format(self.path, str(err)))
            self.send_error(500, "Error processing posted values.")
            return
        self.controller.process_request(None, path_request[0], path_request[1], post_parameters)
    
    
    def parse_POST(self):
        ctype, pdict = parse_header(self.headers['content-type'])
        
        if ctype == 'multipart/form-data':
            postvars = urllib.parse.parse_multipart(self.rfile, pdict)
        elif ctype in ["application/x-www-form-urlencoded", 'application/json']:
                length = int(self.headers['content-length'])
                
                # Place the posted data into postvars for detailed processing.
                postvars = urllib.parse.parse_qs(self.rfile.read(length), keep_blank_values=True)
        else:
            raise HTTPException("Posted content-type not recognized.",500)
        
        return postvars
        
        
    
    @classmethod
    def ValidateURL(cls, path):
        """ValidateURL:  checks to see if the given URL is valid request for
        Historia's web server. If the URL is valid return a dict with the 
        parsed URL.
        
        Valid URLS are defined by the controller and split verions are stored in
        HistoriaHTTPHandler.patterns
        """
        
        # if there is a trailing slash, remove it
        if path[-1:] == '/':
            path = path[:-1]
        
        # push the URL to lowercase to avoid case issues, and split it into segments:
        segments = path.casefold().split('/')
        
        # String should start with / which means an empty string as the first element of the list
        if segments[0] != '' :
            raise HTTPException("Invalid URL sent for validation", 403)
        else:
            segments = segments[1:]
        
        if HistoriaHTTPHandler.url_namespace is not None and HistoriaHTTPHandler.url_namespace != '':
            if segments[0] != HistoriaHTTPHandler.url_namespace:
                raise HTTPException("Invalid URL sent for validation: required namespace missing", 404)
            else:
                segments = segments[1:]
        
        # Check for special cases
        if len(segments) == 0:
            return ('home',None)
        elif segments[0] in HistoriaHTTPHandler.special_cases:
            return (segments[0], '/'.join(segments[1:]))
        
        # There should be only two segments left in the path: object/request
        if len(segments) != 2:
            raise HTTPException("Invalid Request Path", 403)
        
        # Compare remaining segments against the valid patterns
        request = "/".join("segments")
        if request not in HistoriaHTTPHandler.patterns:
            raise HTTPException("Location not found: {0}".format(path), 404)
        else:
            return (segments[0], segments[1])



