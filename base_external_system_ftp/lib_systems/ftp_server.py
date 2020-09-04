# Copyright 2020 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from ftplib import FTP, error_perm

from .abstract_ftp_server import AbstractFTPServer


class FTPServer(AbstractFTPServer):

    _name = "ftp.system.adapter"
    _description = "FTP System Adapter"

    def get_client(self):
        """Return a usable client representing the remote system."""
        server = FTP()
        server.connect(self.external_system.host, self.external_system.port)
        server.login(self.external_system.username, self.external_system.password)
        return server

    def destroy_client(self):
        """Perform any logic necessary to destroy the client connection.

        Args: client (mixed): The client that was returned by ``get_client``.
        """
        self.client_instance.quit()

    def _cd(self, remote_path):
        """Change remote directory."""
        self.client_instance.cwd(remote_path)

    def _test_connection(self):
        """Test wether we can connect to os. Feedback to user handled by super class."""
        with self.client():
            pass

    def putfo(self, file_like, name):
        """Transfer file-like object to server

           name: filename+extension for file at server
           file_like: byte object, content of which
           will appear in server as name

           Example

           bytes_ = b'abc def'
           name = "abc.txt"
           self.putfo(io.BytesIO(bytes_), name)
        """
        self.client_instance.storbinary("STOR " + name, file_like)

    def put(self, filepath, name):
        """Transfer file object to server

           name: filename+extension for file at server
           filepath: path + the actual file you are putting
        """
        with open(filepath, "rb") as file:
            self.client_instance.storbinary("STOR " + name, file)

    def getfo(self, filepath, name):
        """Get file-like object from server

           name: containt of file in filepath in bytes
           filepath: filename+extension for file at server
        """
        self.client_instance.retrbinary("RETR " + filepath, name.write)

    def remove(self, file):
        """Remove file from server"""
        self.client_instance.delete(file)

    def listdir(self, path=""):
        """ List directory in path """
        files = []
        try:
            files = self.client_instance.nlst(path)
        except error_perm:
            files = []
        return files

    def exists(self, file, path=""):
        """ See if file exists in path """
        return file in self.client_instance.nlst(path)
