To use this module, you need to:

1. Neutralize the database (`odoo-bin neutralize`, or a copy neutralized by the database manager or by Odoo.sh): the anonymization refuses to run on a database without the `database.is_neutralized` parameter, so that it cannot overwrite production data
2. Go to Settings / Technical / Anonymization / Run Anonymization
3. Confirm you really mean it

The above is only for testing configurations on small databases: the run happens inside a web request, and on a real-size database it outlasts the HTTP worker's time limit (`limit_time_real`, 120 seconds by default). Usually you would script this on a clone of the production database, before handing it over:

```
odoo-bin neutralize -d clone
odoo-bin shell -d clone <<'END'
env['ir.module.module'].search([('name', '=', 'base_anonymize')]).button_immediate_install()
env['anonymize.wizard'].action_run()
env.cr.commit()
END
```

then dump the database and copy the file store.

The log has one line per definition, with its XML id, its domain, the rows touched and the time taken, so that a slow definition can be spotted.

**!!CAUTION!!** The default configuration replaces the database secret and gives all users the same random password, stored in the system parameter `base_anonymize.password`. The administrator's login becomes `admin`. If you run it from the user interface you will be logged out.
