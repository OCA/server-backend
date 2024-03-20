* much better UX for configuring collections (probably provide a group that sees the current fully flexible field mappings, and by default show some dumbed down version where you can select some preselected vobject fields)
* support todo lists and journals
* support configuring default field mappings per model
* support plain WebDAV collections to make some model's records accessible as folders, and the records' attachments as files (r/w)
* support configuring lists of calendars so that you can have a calendar for every project and appointments are tasks, or a calendar for every sales team and appointments are sale orders. Lots of possibilities

Backporting this to <=v10 will be tricky because radicale only supports python3. Probably it will be quite a hassle to backport the relevant code, so it might be more sensible to just backport the configuration part, and implement the rest as radicale auth/storage plugin that talks to Odoo via odoorpc. It should be possible to recycle most of the code from this addon, which actually implements those plugins, but then within Odoo.
