To configure this module, you need to go to *Settings / API Client / Connections*,
and create a new connection

When using SFTP, the server host public key must be provided.
You can find it with: ``ssh-keygen <hostname>``.
Use the bytes at the end of the line, after the algotrithm (``ssh-rsa`` for example).
