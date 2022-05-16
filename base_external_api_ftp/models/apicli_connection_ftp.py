# Copyright (C) 2022 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import ftplib
import logging
import os
import shutil
import tempfile
from io import BytesIO

import pysftp

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ApicliConnection(models.Model):
    _inherit = "apicli.connection"

    connection_type = fields.Selection(
        selection_add=[("ftp", "FTP"), ("sftp", "SFTP")],
        ondelete={"ftp": "set default", "sftp": "set default"},
    )

    def _delete_file_ftp(self, ftp_session, message):
        if self.connection_type in ["ftp", "sftp"]:
            if self.connection_type == "ftp":
                ftp_rm = ftp_session.delete
            else:
                ftp_rm = ftp_session.remove
            try:
                delete_msg = ftp_rm(message.endpoint)
                message.write({"state": "todo"})
                _logger.info("%s: %s" % (message.endpoint, delete_msg))
            except ftplib.error_perm as delete_msg:
                message.write({"state": "cancel"})
                _logger.info("%s: %s" % (message.endpoint, delete_msg))
            return True

    def _download_each_file(self, subdirectory, ftp):
        ftp.cwd(subdirectory)
        # List of FTP server files in subdirectory
        for file_name in ftp.nlst():
            file_path = subdirectory + "/" + file_name
            # Read File content
            with BytesIO() as r:
                ftp.retrbinary("RETR " + file_path, r.write)
                content = r.getvalue()
                message = self.env["apicli.message"].create(
                    {
                        "connection_id": self.id,
                        "endpoint": file_path,
                        "content": content,
                        "state": "draft",
                    }
                )
                self._delete_file_ftp(ftp, message)
            # Download remote file
        #  ftp.retrbinary("RETR " + file_name, open(file_path, "wb").write)

        # # FIXME: list the FTP server files in subdirectory, not local files!
        # from_path, subdir_list, file_list = next(os.walk(subdirectory))
        # for file_name in file_list:
        #     file_path = os.path.join(from_path, file_name)
        #     # FIXME dowload remote file and read its content, not a local file
        #     with open(file_path, "r") as open_file:
        #         content = open_file.read()
        #     message = self.env["apicli.message"].create(
        #         {
        #             "connection_id": self.id,
        #             "endpoint": file_path,
        #             "content": content,
        #             "state": "draft",
        #         }
        #     )
        #     self._delete_file_ftp(ftp, message)

    @api.model
    def cron_download_ftp_files(self, subdirectory="/", conn_code=None):
        if conn_code is None:
            conn_code = "DemoFTP"
        for conn in self.get_by_code(conn_code, error_when_not_found=False):
            if conn.connection_type == "ftp":
                with ftplib.FTP() as ftp:
                    ftp.connect(conn.address)
                    response = ftp.login(conn.user, conn.password)
                    _logger.debug("FTP connection: %s" % (response))
                    conn._download_each_file(subdirectory, ftp)
            elif conn.connection_type == "sftp":
                with pysftp.Connection(
                    conn.address, username=conn.user, password=conn.password
                ) as sftp:
                    conn._download_each_file(subdirectory, sftp)
        return True

    @api.model
    def _ftp_upload_directory(self, ftp_session, from_local_dir, to_server_dir):
        """
        Given a local directory, upload all files and subdirs.
        - change server work directory
        - search files in local directory, and upload them
        - search subdirs in local directory, and recursively upload them
        """
        # List and upload files
        ftp_session.cwd(to_server_dir)
        from_path, subdir_list, file_list = next(os.walk(from_local_dir))
        for file_name in file_list:
            file_path = os.path.join(from_path, file_name)
            with open(file_path, "rb") as file_obj:
                ftp_session.storlines("STOR %s" % file_name, file_obj)
        for subdir in subdir_list:
            if subdir not in ftp_session.nlst():
                ftp_session.mkd(subdir)
            self._ftp_upload_directory(
                ftp_session, os.path.join(from_local_dir, subdir), subdir
            )

    def _send_ftp_upload(self, from_local_dir, to_server_dir="Inbox"):
        """Send (S)FTP files to the temp.

        This method is used to upload all file in temp directory.
        """
        self.ensure_one()
        if self.connection_type == "ftp":
            with ftplib.FTP() as ftp:
                ftp.connect(self.address)
                response = ftp.login(self.user, self.password)
                _logger.info("FTP: %s" % (response))
                # if no local dir given, just try connection and exit
                if from_local_dir:
                    self._ftp_upload_directory(ftp, from_local_dir, to_server_dir)
        elif self.connection_type == "sftp":
            with pysftp.Connection(
                self.address, username=self.user, password=self.password
            ) as sftp:
                _logger.info("SFTP: local_dir %s", from_local_dir)
                if from_local_dir:
                    sftp.put_r(from_local_dir, to_server_dir, preserve_mtime=True)

    def api_test(self):
        if self.connection_type == "ftp" or self.connection_type == "sftp":
            # Interruped with an error if connection fails
            self._send_ftp_upload(None)
        return super().api_test()

    def _send_ftp_files(self, file_dict):
        """Send the files to the backend.

        :param file_dict dictionary with 'name' for the filename and
        'content' for the content
        :return: A dictionary with:
         - a boolean 'success': True if the transfer was successful,
          False otherwise
         - a string 'message': Message to be displayed to the end user
         - a string 'ref': Reference of the transfer to request the status
        """
        temp_dir = tempfile.mkdtemp()
        _logger.info("FTP uploading %d files from %s", len(file_dict), temp_dir)
        for file_path, file_content in file_dict.items():
            if file_path.startswith("/"):
                file_path = file_path[1:]
            file_dir, file_name = os.path.split(file_path)
            full_dir = os.path.join(temp_dir, file_dir)
            full_path = os.path.join(full_dir, file_name)
            os.makedirs(full_dir, exist_ok=True)
            with open(full_path, "w") as file_obj:
                file_obj.write(file_content)
        self._send_ftp_upload(temp_dir)
        shutil.rmtree(temp_dir)
        return {"success": True, "message": "OK"}

    def api_call_raw(
        self,
        endpoint,
        verb="GET",
        headers_add=None,
        params=None,
        payload=None,
        suppress_errors=None,
        token=None,
        **kwargs,
    ):
        if self.connection_type in ("ftp", "sftp"):
            _logger.debug("\nSFTP upload to %s:\n%s", endpoint, payload)
            return self._send_ftp_files({endpoint: payload})
        return super().api_call_raw(
            endpoint,
            verb=verb,
            headers_add=headers_add,
            params=params,
            payload=payload,
            suppress_errors=suppress_errors,
            token=token,
            **kwargs,
        )
