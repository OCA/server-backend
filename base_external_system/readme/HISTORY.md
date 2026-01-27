## Version 16.0.1.0.0

Migration to 16.0

## Version 16.0.2.0.0

Model base.external.system will be the only regular model, containing
all the data. 

If people have used this module "as is" to store connection data, no changes
will be needed. In case anybody has implemented a specific interface,
this would need to be changed to an abstract class that inherits from
external.system.adapter, using the example of `external.system.adapter.os`.
