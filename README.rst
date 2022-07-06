Bill Validator Driver
=============================

This is the repository for `Biller Validator`, a simple driver for the NV9USB bill
validator using the SSP (unencrypted) protocol. Note that not all features may
be available.

Developer guide
---------------

`pipenv <https://docs.pipenv.org>`_ is used for dependency management, so first
of all make sure you have it installed::

    python -m pip install pipenv

Once you have it, simply run ``pipenv`` on the repository directory to set
everything up::

    pipenv install --dev

and then open a shell on the recently created Python virtual environment::

    pipenv shell

Now you can run any of the examples, e.g.::

    cd main
    
Now you want to install all the requirements from the requirements.txt file using the following command::

    pip install -r requirements.txt

After successful installation of all the installations you can run the application using the following command::

    python app.py

