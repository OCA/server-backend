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
- Edit ``/etc/ssh/sshd_config``, 

Make sure that the line ``PasswordAuthentication no``, if any, is commented (to allow for user/password connection to ssh server).
Then append the following
  .. code-block::

     Match group sftp
     ChrootDirectory /home
     X11Forwarding no
     AllowTcpForwarding no
     ForceCommand internal-sftp

- (Res)start the service: ``sudo service ssh restart``
- Test the connection with ``sftp myuser@localhost``.
  
If when testing the connection you get a message saying: "Unable to ssh localhost: Permission denied (publickey)" try the following steps: (from https://stackoverflow.com/questions/28210637/unable-to-ssh-localhost-permission-denied-publickey-connection-closed-by)

If you're running Ubuntu on Windows Subsystem for Linux, there will not be a preinstalled public key or authorized keys list, so you'll need to generate your own.

If you don't already have openssh-server installed:

1. ``sudo apt-get upgrade``
2. ``sudo apt-get update``
3. ``sudo apt-get install openssh-server``
4. ``sudo service ssh start``

Then take the following steps to enable sshing to localhost:

5. ``cd ~/.ssh``
6. (skip this step if you already have a ssh key pair generated) ``ssh-keygen`` (to generate a public/private rsa key pair; use the default options)
7. ``cat id_rsa.pub >> authorized_keys`` (to append the key to the authorized_keys file)
8. ``chmod 640 authorized_keys`` (to set restricted permissions)
9. ``sudo service ssh restart`` (to pickup recent changes)
10. ``ssh localhost``







  The FTP default work directory will be your home directory.
