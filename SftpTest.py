import datetime
import socket
import traceback
import paramiko
import sys
import os

class Paramiko_SFTP(object):
    def __init__(self,server_ip):
        self.username='root'
        self.passed='XLuo+Agi198244'
        self.server_ip=server_ip
        self.port=22

    def put_dir_files(self,local_dir,remote_dir):
        if os.path.isdir(local_dir):
            for file in os.listdir(local_dir):
                if (file[0]=='.'):
                    continue
                new_local_dir=local_dir+"\\"+file
                new_remote_dir=remote_dir+file
                self.put_file(new_local_dir,new_remote_dir)
                print '\t\tupload:'+file+" to "+self.server_ip+":"+new_remote_dir


    def put_file(self,local_dir,remote_dir):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.server_ip, self.port))
        except Exception, e:
            print '*** Connect failed: ' + str(e)
            traceback.print_exc()
            sys.exit(1)
        t = paramiko.Transport(sock)
        try:
            t.start_client()
        except paramiko.SSHException:
            print '*** SSH negotiation failed.'
            sys.exit(1)
        keys = {}
        key = t.get_remote_server_key()
        t.auth_password(self.username, self.passed)
        sftp = paramiko.SFTPClient.from_transport(t)
        d = datetime.date.today() - datetime.timedelta(1)
        sftp.put(local_dir, remote_dir,callback=self.progress_bar)
        sftp.close()
        t.close()

    def progress_bar(self,transferred, toBeTransferred, suffix=''):
        bar_len = 60
        filled_len = int(round(bar_len * transferred / float(toBeTransferred)))
        percents = round(100.0 * transferred / float(toBeTransferred), 1)
        bar = '=' * filled_len + '-' * (bar_len - filled_len)
        sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
        sys.stdout.flush()



if __name__ == '__main__':
    TestSftp=Paramiko_SFTP('120.25.199.28')
    TestSftp.put_dir_files(os.getcwd(),'/home/agent/test/')