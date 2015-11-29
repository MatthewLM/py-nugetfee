py-nugetfee
===========

A simple WSGI application to provide NuBits fees over HTTP given a transaction size and the total output amount.

##Installation

This project requires coin-rpc-client: https://gitlab.com/TokenLabs/coin-rpc-client
It also requires that mod_wsgi is installed and enabled for your apache installation.

First clone this project and the coin-rpc-client project. In each project directory do this:

```
sudo python3 setup.py install
```

Create a file containing:

```
#!/bin/python3
from pynugetfee import Application
application = Application()
```

Add the following to the virtualhost configuration, replacing necessary capitals parts:

```
WSGIScriptAlias /PATH_TO_GET_VALID_HASHES/getfee /PATH/TO/PYTHON/FILE/CREATED.py

WSGIDaemonProcess nubits_mod_wsgi user=USERNAME
WSGIProcessGroup nubits_mod_wsgi
```

Note that the /getfee path is necessary to be compatible with NuDroid, as NuDroid will add "/getfee" 
onto the end of the trusted server API. PATH_TO_GET_VALID_HASHES should be the same as the path to
the trusted server URL for Nudroid. However this is optional if only providing a basic API interface.

You may also need to give access permissions to the script directory.

Reload apache and you are good to go.
