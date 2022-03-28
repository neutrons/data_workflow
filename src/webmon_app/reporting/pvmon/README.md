PVMON web monitor
-----------------

Defines the data structure to hold Epics PVs and present them on the web monitor.


## Data handling
- The pvmon part of the web monitor only reports on the data put into it's tables.
The data is entered by DASMON, which uses the stored procedure defined in
`pvmon/sql/stored_procs.sql`.

- TODO: pvmon needs to remove entries older than a week.

- TODO: Create a cache table for easy access to latest value of each parameter.
