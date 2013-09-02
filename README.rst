PyPLN
=====

PyPLN is a distributed pipeline for natural language processing, made in Python.
We use `NLTK <http://nltk.org/>`_ and `ZeroMQ <http://www.zeromq.org/>`_ as
our foundations. The goal of the project is to create an easy way to use NLTK
for processing big corpora, with a REST API.

PyPLN is sponsored by `Fundação Getulio Vargas <http://portal.fgv.br/>`_.

License
-------

PyPLN is free software, released under the GPLv3
`<https://gnu.org/licenses/gpl-3.0.html>`_.

Using
-----

You can start by looking at our `quickstart guide
<https://github.com/NAMD/pypln.web/wiki/Quickstart-guide>`_.

Installing
----------

To install dependencies (on a Debian-like GNU/Linux distribution)::

    sudo apt-get install python-setuptools mongodb
    pip install virtualenv virtualenvwrapper
    mkvirtualenv pypln.web
    pip install -r requirements/production.txt

You will also need to install NLTK data. You can do so following the `NLTK
documentation <http://nltk.org/data.html>`_.


Developing
----------

To run tests::

    workon pypln.web
    pip install -r requirements/development.txt
    make test



To run the development webserver::

    workon pypln.web
    pip install -r requirements/project.txt
    ./manage.py runserver --settings=pypln.web.settings.development

See our `code guidelines <https://github.com/namd/pypln.web/blob/develop/CONTRIBUTING.rst>`_.
