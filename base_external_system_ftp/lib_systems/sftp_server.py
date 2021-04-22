# Copyright 2020 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import pysftp

from .abstract_ftp_server import AbstractFTPServer


class SFTPServer(AbstractFTPServer):

    _name = "sftp.system.adapter"
    _description = "SFTP System Adapter"

    def get_client(self):
        """Return a usable client representing the remote system."""
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        server = pysftp.Connection(
            self.external_system.host,
            self.external_system.port,
            self.external_system.username,
            self.external_system.password,
            cnopts=cnopts,
        )
        return server

    def destroy_client(self):
        """Perform any logic necessary to destroy the client connection.

        Args: client (mixed): The client that was returned by ``get_client``.
        """
        self.client_instance.close()

    def _cd(self, remote_path):
        """Change remote directory."""
        self.client_instance.chdir(remote_path)

    def _test_connection(self):
        """Test wether we can connect to os. Feedback to user handled by super class."""
        with self.client():
            pass

    def putfo(self, file_like, name):
        """Transfer file-like object to server

           name: filename+extension for file at server
           file_like: byte object, content of which
           will appear in server as name
        """
        self.client_instance.putfo(file_like, name)

    def put(self, filepath, name):
        """Transfer file object to server

           name: filename+extension for file at server
           filepath: filepath_to_file, content of which
           will appear in server as name
        """
        self.client_instance.put(filepath, name)

    def getfo(self, name, file_like):
        """Get file from server

        name: filename of file to retrieve
        file_like: byte object to save containt
        of filename
        """
        self.client_instance.getfo(name, file_like)

    def remove(self, file):
        """Remove file from server"""
        self.client_instance.remove(file)

    def listdir(self, path=""):
        """ List directory in path """
        return self.client_instance.listdir(path)

    def exists(self, file, path=""):
        """ See if file exists in path """
        return self.client_instance.exists(path + file)
