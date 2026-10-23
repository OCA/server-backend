Create an external system record and optionally define endpoints.

Example configuration:

* Host: ``api.example.com``
* Remote path: ``/v1``

Define endpoints such as:

* ``status`` → ``/status``
* ``items`` → ``/items``

Use the adapter:

.. code-block:: python

    with system.client() as client:
        response = client.get(endpoint="status")
        response = client.post(endpoint="items", json={"name": "Item"})
        response = client.put(endpoint="items", json={"active": True})

Responses are returned as ``requests.Response`` objects.

Errors raise ``ValidationError`` with detailed messages.
