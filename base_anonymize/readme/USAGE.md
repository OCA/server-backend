To use this module, you need to:

1. Go to Settings / Technical / Anonymization / Run Anonymization
2. Confirm you really mean it

The above is only for testing configurations, usually you would script this in some export setting by installing the module on a clone, possibly a custom module modifying the field configuration, and running the code ``env['anonymize.wizard'].action_run()`` before you export your file store and dump the database to wherever you need it.

**!!CAUTION!!** The default configuration overwrites the database secret and sets all passwords to `password` - for your tests, you will want to disable the field definitions for `res.users` and `ir.config_parameter`, because you'll be logged out after the anonymization run otherwise.
