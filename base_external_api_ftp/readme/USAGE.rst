Suggested setup steps for local tests:

- Locally install FTP service:

  - Install vsftpd: ``sudo apt install vsftpd``.
    Additional documention available at https://help.ubuntu.com/community/vsftpd
  - Edit ``/etc/vsftpd.conf``, changing the entry ``write_enable=YES``
  - (Res)start the service: ``sudo service vsftpd restart``
  - Test the connection with the ``ftp`` client. User you system user and password.
    The FTP default work directory will be your home directory.
