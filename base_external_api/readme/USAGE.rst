This is a technical module, to be leveraged by developers to efficiently develop API
integrations.

The `apicli.connection` Model stores the configured connections.
It provides the logic to send API messages and handle errors.
It also provides helpers to render the messages to send.

For example, to prepare a message for `res.partner`:

    self.api_render_message()
    conn = self.env["apicli.connection"].get_by_code("MYCODE")
