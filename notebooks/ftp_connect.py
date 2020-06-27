from ftplib import FTP
from notebooks.ftp_login import login, password, HOST


def receive_file(remote_path, filename, local_path='data/'):
    ftp = FTP(host=HOST, user=login, passwd=password)
    ftp.login(login, password)  # Login in
    ftp.cwd(remote_path)
    # Receiving file
    ftp.retrbinary(cmd="RETR " + filename,
                   callback=open(local_path + f'input_{filename}', 'wb').write)
    # Closing connection
    ftp.quit()


if __name__ == "__main__":
    path = '/joomla_22/public_html/uploads'
    file = '00.jpg'
    receive_file(remote_path=path, filename=file)
