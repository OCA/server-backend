To use this module:

* Go to *Settings > Database Structure > Database Sources*
* Click on Create to enter the following information:
  * Datasource name
  * Pasword
  * Connector: Choose "SQLAlchemy"
  * Connection string: Specify how to connect to database

To know how to format the connection string:

* Make sure `the dialect you choose
  <https://docs.sqlalchemy.org/en/20/dialects/index.html>`__ is properly
  supported.
* Read `the docs on how to configure the query string
  <https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls>`__.
  These can differ a bit across dialects and engines.
* Make sure you write ``%s`` where the password should be. That will be
  replaced by the password when building the full query string.
