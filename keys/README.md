Historia SSL Setup
==================
A self-signed cert is plenty good enough for testing and development.  Obviously this is not good for production use under the vast majority of conditions. To generate the expected certificate you can use OpenSSL from within this directory:
$ openssl req -x509 -newkey rsa:2048 -keyout historia.pem -out historia.pem -days 2000 -nodes

Historia AES Key
================
AES is used to encrypt user database passwords in the master database.  They key is stored in a file set via the main configuration file, by default that location is keys/database_aes.key, but can be any file readable by the user executing Historia. The key value is a 32-byte string.
You can generate a key by entering the following commands into the python interpreter.
import binascii, os
with open('../keys/database_aes.key', 'wb') as f:
   f.write(binascii.hexlify(os.urandom(32)))
   
