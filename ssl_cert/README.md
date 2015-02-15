Historia SSL Setup
==================
A self-signed cert is plenty good enough for testing and development.  Obviously this is not good for production use under the vast majority of conditions. To generate the expected certificate you can use OpenSSL from within this directory:
$ openssl req -x509 -newkey rsa:2048 -keyout historia.pem -out historia.pem -days 2000 -nodes