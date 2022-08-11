To configure this module, you need to:

#. add section ``[pglogical]`` to your odoo configuration file
#. add value ``replication_sets = set1,set2,set3,etc`` in this section
#. add ``pglogical`` to your list of server wide modules

Example::

    [pglogical]
    replication_sets = ddl_sql
