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

But it's better to use virtualenv for more information look at `<http://flask.pocoo.org/docs/installation/>`__ 

trocr
*******
Just download andextract trocr file to a folder 

.. code-block:: bash

	$ curl -L https://github.com/cypx/trocr/archive/master.tar.gz | tar zx --strip-components=1

Copy configuration file (webconfig.py) from sample (webconfig.py.sample) an modify it as you want

.. code-block:: bash

	$ cp webconfig.py.sample webconfig.py
	$ vi 

For quick test you could use:

.. code-block:: bash

	$ python trocr.py

Refer to your web server documentation about WSGI for production use
