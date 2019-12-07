from ftplib import FTP
from ftp_login import login, password

HOST = '92.53.96.122'
PORT = 21

ftp = FTP(host=HOST, user=login, passwd=password)
ftp.login(login, password)

path = '/joomla_22/public_html/uploads'
filename = '00.jpg'
# Receiving files
ftp.cwd(path)
ftp.retrbinary(cmd="RETR " + filename,
               callback=open(filename, 'wb').write)
# Closing connection
ftp.quit()
