This module provides an HTTP(S) adapter for the ``base_external_system`` framework.

It allows Odoo to communicate with external systems over HTTP using a consistent
adapter interface, supporting GET, POST and PUT requests, endpoint resolution,
and connection testing.

The adapter itself acts as the client and is yielded via the standard
``system.client()`` context manager.
