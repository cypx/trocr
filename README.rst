**********************************
TROCR  - Share your file 
**********************************

**trocr** is a file sharing web application based on Flask framework 

Installation
##############

Flask framework
*****************

Flask framework is needed for running trocr.
Could be installed on Debian/Ubuntu by this commands

.. code-block:: bash

	$ aptitude install python-pip
	$ easy_install flask

For more information look at `<http://flask.pocoo.org/docs/installation/>`__ 

trocr
*******
Just download andextract trocr file to a folder 

.. code-block:: bash

	$ curl -L https://github.com/cypx/trocr/archive/master.tar.gz | tar zx --strip-components=1

And for quick test use:

.. code-block:: bash

	$ python trocr.py

Refer to your web server documentation about WSGI for production use
