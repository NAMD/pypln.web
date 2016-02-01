# PyPLN

[![PyPi version](https://img.shields.io/pypi/v/pypln.web.svg)](https://crate.io/packages/pypln.web/)
[![PyPi downloads](https://img.shields.io/pypi/dm/pypln.web.svg)](https://crate.io/packages/pypln.web/)

PyPLN is a distributed pipeline for natural language processing, made in
Python.

PyPLN.Web is the PyPLN's interface to the world: you use it as an HTTP REST
API.


## Using

You can start by looking at our [quickstart
guide](https://github.com/NAMD/pypln.web/wiki/Quickstart-guide).


## Installing

To install dependencies (on a Debian-like GNU/Linux distribution), execute:

    sudo apt-get install python-setuptools mongodb
    pip install virtualenv virtualenvwrapper
    mkvirtualenv pypln.web
    pip install -r requirements/production.txt
    cp pypln/web/settings.ini{.sample,}


## Developing

To run all tests, you'll need the elasticsearch server running. You can find
[detailed instructions for your platform in their
documentation](https://www.elastic.co/downloads/elasticsearch). After that, you
can just run:

    workon pypln.web
    pip install -r requirements/development.txt
    python manage.py test --settings=pypln.web.settings.test


To run the development webserver:

    workon pypln.web
    python manage.py runserver --settings=pypln.web.settings.development


If your repository is inside the virtualenv directory, there are some helpers:

    source contrib/postactivate # load the helper functions
    manage_test test # `manage_test` will run any comand (`test` in this case)
                     # with the test settings.
    manage_dev runserver # `manage_dev` is similar, but uses the development
                         # settings

See our [code guidelines](https://github.com/namd/pypln.web/blob/develop/CONTRIBUTING.rst).


## License

PyPLN is free software, released under the [GNU General Public License version
3](https://gnu.org/licenses/gpl-3.0.html).


## Sponsor

PyPLN development is made at [Applied Math School/FGV](http://emap.fgv.br/) and
sponsored by [Fundação Getulio Vargas](http://portal.fgv.br/).
