DASMON web monitor
-----------------

Defines the data structure to hold DASMON information and report on it.


## Data handling
- The dasmon part of the web monitor reports on messages sent to ActiveMQ
by DASMON. The database tables for dasmon are populated by the `dasmon_listener`.

- Entries older than a week are deleted from the tables.
