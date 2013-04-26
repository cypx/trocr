**********************************
TROCR  - Share your file
**********************************

**trocr** is a file sharing web application based on `Flask framework <http://flask.pocoo.org>`_

|flattr|_

Features
##############

* multiple files upload
* gallery page creation
* HTML & BBCode link generation with thumbnail for image
* HTML & BBCode link generation for all file
* HTML video player and audio player for supported file

Example & demo
#################

* gallery sample: `<http://trocr.bidouille.info/?g=d4641421-13fa-424b-87ae-4fb7c2a44ca7>`__
* demo (automatically resets every 10mn): `<http://trocr-demo.bidouille.info/>`__ (login/pass = demo/demo)

Installation
#################

Flask framework
******************

Flask framework is needed for running trocr.
Could be installed on Debian/Ubuntu by this commands

.. code-block:: bash

	$ aptitude install python-pip
	$ easy_install flask

Python Imaging Library (PIL) is also required

.. code-block:: bash

	$ easy_install pil


But it's better to use virtualenv, quick example (including trocr install)

.. code-block:: bash

	$ aptitude install python-pip python-virtualenv
	$ virtualenv --no-site-packages ./path_to_trocr_directory
	$ cd ./path_to_trocr_directory
	$ source ./bin/activate
	$ curl -L https://github.com/cypx/trocr/archive/master.tar.gz | tar zx --strip-components=1
	$ cp websiteconfig.py.sample websiteconfig.py
	$ pip install -Ur requirements.txt
	$ python trocr.py

For more information look at `<http://flask.pocoo.org/docs/installation/>`__

trocr
*******
Just download and extract trocr file to a folder

.. code-block:: bash

	$ curl -L https://github.com/cypx/trocr/archive/master.tar.gz | tar zx --strip-components=1

Create configuration file (webconfig.py) from sample (webconfig.py.sample) an modify it as you want

.. code-block:: bash

	$ cp webconfig.py.sample webconfig.py
	$ vi webconfig.py

For quick test you could use:

.. code-block:: bash

	$ python trocr.py

Refer to `<http://flask.pocoo.org/docs/deploying/>`__  and your web server documentation about WSGI for production use

MediaElements
******************

If you want to enable `MediaElements.js<http://mediaelementjs.com/>`_ first you need to download and extract it's build folder content into static/mediaelement directory:

.. code-block:: bash

	$ mkdir static/mediaelement
	$ cd static/mediaelement
	$ curl -L https://github.com/johndyer/mediaelement/archive/master.tar.gz | tar zx --strip-components=2 --wildcards "*/build/*"

After that do not forget to activate it into webconfig.py

.. code-block:: python

	ENABLE_MEDIAELEMENT = True

.. |flattr| image:: http://api.flattr.com/button/flattr-badge-large.png
 :alt: Flattr this git repo
.. _flattr: https://flattr.com/submit/auto?user_id=cypx&url=https://github.com/cypx/trocr&title=trocr&language=&tags=github&category=software