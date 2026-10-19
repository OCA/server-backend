- Go to Settings \> Technical \> Database Structure \> Database Sources
- Click on Create to enter the following information:
- Data source name 
- Password
- Connector: Choose the database to which you want to connect
- Connection string: Specify how to connect to database


Use developer mode and an administrator account to manage database sources.
Sources are restricted to their company; sources without a company are shared.
For PostgreSQL, enter a libpq connection string, for example:

```text
dbname='external' user='reader' host='database' port='5432' password=%s connect_timeout=5
```

Enter the password in its separate field. Use **Test Connection** to verify the
configuration. The result is displayed in a dialog. Database credentials should
have only the permissions needed for the intended queries.

From server-side code, call `source.execute(query, execute_params)` with bound
parameters. Pass `metadata=True` to return both `rows` and `cols`. The addon
closes the external connection after each operation.
