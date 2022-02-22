DASMON Listener
---------------

ActiveMQ client that listens to DASMON messages and logs them into a database.

## Pre-requisites
- Install ActiveMQ ([http://activemq.apache.org/](http://activemq.apache.org/))
- stomp.py (version 3.3.1 or higher) should be installed to enable ActiveMQ communication ([http://code.google.com/p/stomppy/](http://code.google.com/p/stomppy/))

## Installation and configuration
- The `dasmon_listener` will be installed as a python module.

- It should be configured by creating a file `dasmon_listener/local_settings.py`
that contains the ActiveMQ credentials, the topics to listent to, and the instrument short name:


		brokers = [("localhost", 61613)]
		amq_user = "icat"
		amq_pwd = "icat"

		queues = ["/topic/ADARA.APP.DASMON.0",
	    	      "/topic/ADARA.STATUS.DASMON.0",
	        	  "/topic/ADARA.SIGNAL.DASMON.0"]

		instrument_shortname = 'hysa'

		PURGE_TIMEOUT = 7


	The `PURGE_TIMEOUT` parameter is the number of days after which key-value pairs will be removed from the database.


- The `dasmon_listener/local_settings.py` file should be put in the source directory BEFORE
executing `make install`.

- The setup.py script will not only install the `dasmon_listener` module, but will
also create a script named `dasmon_listener` at a location where it can be
used by all users.
In the event that the `dasmon_listener` script is not installed on the
system path, you can use the `--install-scripts` option when running
the installation script:

        python setup_dasmon_listener.py install --install-scripts /usr/local/bin
