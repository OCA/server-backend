To configure a connection that uses a Client Assertion two objects are needed.

1. An Oauth definition that can be configured through:
   Settings ==> Users & Companies ==> Oauth Providers.

   Create an Oauth definition with the following information:
   - Provider Name: any name you like;
   - Client Id: provided by Microsoft;
   - Tenant: provided by Microsoft;
   - Provider type: Microsoft Client Assertion;
   - Client Secret: leave blank;
   - Allowed: False / unchecked (This will not be used to log into Odoo);
   - Login button label: required but irrelevant, just add some text;
   - Css class: irrelevant, leave at default;
   - Login button label: required but irrelevant, just add some text;
   - Authorization url: https://login.microsoftonline.com;
   - Scope: provided by microsoft, but replace Client Id part with '%s';
   - User info url: required but irrelevant, just add some text;
   - Date endpint: leave blank.

   Provided by microsoft usually means provided by the systems administrator of
   the company to whose applications you want to connect using the client assertion.

2. An external system definition that can be configured through:
   Settings ==> Technical ==> External Systems.

   Create an external system definition with the following information:
   - Name: any name you like;
   - Host: the host that contains the application you want to connect to;
   - System type: Oauth for Microsoft Client Assertion;
   - OAuth definition: select the definition created above;
   - Private key: name of the private key file stored in filesystem. See below;
   - Private key password: password for the private key;
   - Private key thumbprint: provided by the certificate authority.

For security reasons the private key is not stored in the database and not shown on the
web. It has to be placed in your datadirectory alongside the attachment directories in
a directory called keystore that you must create manually. The full path will be
as follows:
<odoo data directory>/filestore/<database name>/keystore/<filename>

In the field 'Private key' just store the bare filename, not a path.

You create the private key yourself using openssl, like so:
$ openssl genrsa -out mykey.key 2048

However to get a client assertion, you need a signed public certificate that can be
send to Microsoft (by yourself, or by the company you want to connect to).
The certificate signing request can be generated like so:
$ openssl req -new -key mykey.key -out myrequest.csr

Send the request to your preferred Certificate Authority and you will receive
a public certificate along with a thumbprint.

