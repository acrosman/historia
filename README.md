# Historia
Historia is a web based application to support large research projects for historians and other humanities researchers.

Setup
=====
Historia uses HTTPS for all connections, and therefore uses a certificate. By default the system looks for ssl_cert/historia.pem within the project root.  See README in that directory for more information.

Starting Historia
=================
Historia uses a built-in web server, and currently has no configuration (something that will change soon). To start the web server on a local machine simply browse to the historia/src folder in a command line window and run ./historia.  Then in your web browser open: https://localhost:8080/historia

Requirements
============
**Python 3.4**
Historia's should run on any platform that supports Python 3.4 or later, but it has only been tested on MacOS X. 

The following add-ons are required:
**py-bcrypt**
https://code.google.com/p/py-bcrypt/

**mysql python connector**
http://dev.mysql.com/downloads/connector/python/

License
=======
Historia is licensed under GPL 3.0