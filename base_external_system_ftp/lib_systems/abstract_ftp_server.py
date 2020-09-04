# Copyright 2020 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from abc import abstractmethod

from odoo.addons.base_external_system.lib_systems.external_system_adapter import (
    ExternalSystemAdapter,
)


class AbstractFTPServer(ExternalSystemAdapter):
    """Add further methods to Abstract System adapter for FTP servers."""

    _name = "abstract.ftp.system.adapter"
    _description = "Abstract FTP System Adapter"

    @abstractmethod
    def putfo(self, file_like, name):
        """Transfer file-like object to server

           name: filename+extension for file at server
           file_like: byte object, content of which
           will appear in server as name
        """
        raise NotImplementedError

    @abstractmethod
    def put(self, filepath, name):
        """Transfer file object to server

           name: filename+extension for file at server
           filepath: path + the actual file you are putting
        """
        raise NotImplementedError

    @abstractmethod
    def getfo(self, file_like, name):
        """Get file from server

        name: filename of file to retrieve
        file_like: byte object to save containt
        of filename
        """
        raise NotImplementedError

    @abstractmethod
    def remove(self, file):
        """Remove file from server"""
        raise NotImplementedError

    @abstractmethod
    def listdir(self, path=""):
        """ List in current directory """
        raise NotImplementedError

    @abstractmethod
    def exists(self, file, path=""):
        """ See if file exists in path """
        raise NotImplementedError
