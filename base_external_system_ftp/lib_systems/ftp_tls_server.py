# Copyright 2020 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from ftplib import FTP_TLS

from .ftp_server import FTPServer


class FTPTLSServer(FTPServer):

    _name = "ftptls.system.adapter"
    _description = "FTPTLS System Adapter"

    def get_client(self):
        """Return a usable client representing the remote system."""
        server = FTP_TLS()
        server.connect(self.external_system.host, self.external_system.port)
        server.login(self.external_system.username, self.external_system.password)
        return server
