Installation
============

Standard
--------

The recommended way to install the libary, is as follows:

.. code-block::

    pip install -U arez

If you'd be having problems invoking ``pip``, you can also try running it as a module, like so:

.. code-block::

    python -m pip install -U arez

The same command can be used to install an update, if there would be one available.

Advanced
--------

To install the development version of the libary, point the install at the dev branch
of the github repo:

.. code-block::

    pip install --force-reinstall git+https://github.com/DevilXD/aRez@dev

Make sure to then refer to the development version of the documentation:
https://arez.readthedocs.io/en/dev/

.. warning::

    The development version may be unstable and contain breaking changes, but also give access
    to new and upcoming functionality. In most cases though, it's recommended to install the
    standard version instead.

    **Use it at your own risk.**
