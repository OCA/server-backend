# Copyright 2020 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _
from odoo.exceptions import UserError

from .abstract_ftp_server import AbstractFTPServer


class MockServer(AbstractFTPServer):
    """Define a Mock FTP server that stores and retrieves files from memory.

    The purpose it not so much to unittest the server_ftp module, but rather the
    modules that use this module, without need for an external connection.

    You will need to put files first, before using any get functions.
    """

    _name = "mock.ftp.system.adapter"
    _description = "Mock FTP System Adapter"

    def __init__(self, external_system):
        super().__init__(external_system)
        self.filestore = None  # To hold file-objects in memory
        self.current_directory = None

    def get_client(self):
        """Return a usable client representing the remote system."""
        self.filestore = {"/": {}}  # One "directory" with no files.
        self.current_directory = "/"
        return self

    def destroy_client(self):
        """Perform any logic necessary to destroy the client connection.

        Args: client (mixed): The client that was returned by ``get_client``.
        """
        self.filestore = None
        self.current_directory = None

    def _cd(self, remote_path):
        """Change directory, automatically create it if not existing."""
        if remote_path not in self.filestore:
            self.filestore[remote_path] = {}
        self.current_directory = remote_path

    def _test_connection(self):
        """FOr the moment connection with mock server will always succeed."""
        with self.client():
            pass

    def putfo(self, file_like, name):
        """Transfer file-like object to server

           name: filename+extension for file at server
           file_like: byte object, content of which
           will appear in server as name
        """
        directory = self._get_checked_directory()
        file_like.seek(0)
        directory[name] = file_like.read()

    def put(self, filepath, name):
        """Transfer file object to server

           name: filename+extension for file at server
           filepath: filepath_to_file, content of which
           will appear in server as name
        """
        localfile = open(filepath, "rb")
        self.putfo(localfile, name)
        localfile.close()

    def getfo(self, name, file_like):
        """Get file from server

        name: filename of file to retrieve
        file_like: byte object to save containt
        of filename
        """
        directory = self._get_checked_directory()
        return file_like.write(directory[name])

    def remove(self, file):
        """Remove file from server"""
        directory = self._get_checked_directory()
        del directory[file]

    def listdir(self, path=""):
        """ List directory in path """
        directory = self._get_checked_directory(path)
        return list(directory.keys())  # list: otherwise returns dict_keys object.

    def exists(self, file, path="."):
        """ See if file exists in path """
        directory = self._get_checked_directory(path)
        return file in directory

    def _get_checked_directory(self, path=None):
        """Get path, but check for existence."""
        path = path != "." and path or self.current_directory
        if path not in self.filestore:
            raise UserError(_("Path does not exist."))
        return self.filestore[path]
