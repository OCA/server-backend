Suggested setup steps for local tests, in a Debian/Ubuntu system:

To locally install FTP service:

- Install vsftpd: ``sudo apt install vsftpd``.
  Additional documention available at https://help.ubuntu.com/community/vsftpd
- Edit ``/etc/vsftpd.conf``, changing the entry ``write_enable=YES``
- (Res)start the service: ``sudo service vsftpd restart``
- Test the connection with ``ftp myuser@localhost``.
  The FTP default work directory will be your home directory.


To locally install SFTP service:

- Install ssh: ``sudo apt install ssh``
- Edit ``/etc/ssh/sshd_config``, appending the following
  .. code-block::

     Match group sftp
     ChrootDirectory /home
     X11Forwarding no
     AllowTcpForwarding no
     ForceCommand internal-sftp

- (Res)start the service: ``sudo service ssh restart``
- Test the connection with ``sftp myuser@localhost``.
  The FTP default work directory will be your home directory.
