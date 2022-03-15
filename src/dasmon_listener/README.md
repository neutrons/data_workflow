DASMON Listener
---------------

ActiveMQ client that listens to DASMON messages and logs them into a database.

## Pre-requisites
- Install ActiveMQ ([http://activemq.apache.org/](http://activemq.apache.org/))
- stomp.py (version 3.3.1 or higher) should be installed to enable ActiveMQ communication ([http://code.google.com/p/stomppy/](http://code.google.com/p/stomppy/))

## Installation and configuration
- The `dasmon_listener` will be installed as a python module.

- The `dasmon_listener` will try to use two environment variables, `AMQ_BROKER` and `AMQ_QUEUE` to setup the actual brokers and queues.
  - If not provided, it will try to use the one cached in database.
  - If cache from database is empty, it will use the default values (see `settings.py`)

- The setup.py script will not only install the `dasmon_listener` module, but will
also create a script named `dasmon_listener` at a location where it can be
used by all users.
In the event that the `dasmon_listener` script is not installed on the
system path, you can use the `--install-scripts` option when running
the installation script:

        python setup_dasmon_listener.py install --install-scripts /usr/local/bin
