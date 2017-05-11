#encoding=utf-8
import telnetlib
import MySQLdb
import time,re,os

class RTelnet(object):
    def __init__(self,host,report_file):
        self.host=host
        self.port="23"
        self.username='agent'
        self.userpasswd='test'
        self.tn = telnetlib.Telnet(self.host, self.port, timeout=10)
        self.f=report_file

    def login(self):
        self.tn=telnetlib.Telnet(self.host,self.port,timeout=10)
        self.tn.set_debuglevel(2)
        self.tn.read_until('login:')
        self.tn.write(self.username+'\n')
        self.tn.read_until('Password:')
        self.tn.write(self.userpasswd+'\n')
        self.tn.read_until('$')

    def change_root(self):
        self.tn.write("su" + '\n')
        time.sleep(1)
        data = self.tn.read_very_eager()
        if re.search(r'(Password)', data):
            self.tn.write("XLuo+Agi198244" + '\n')
            time.sleep(1)

    def clear_host(self):
        self.change_root()
        self.tn.write("docker rm -f $(docker ps -qa)"+'\n')
        time.sleep(10)
        self.tn.write("rm -rf /var/etcd/" + '\n')
        self.tn.write("tac /proc/mounts | awk '{print $2}' | grep /var/lib/kubelet | xargs umount" + '\n')
        self.tn.write("rm -rf /var/lib/kubelet/" + '\n')
        self.tn.write("tac /proc/mounts | awk '{print $2}' | grep /var/lib/rancher | xargs umount" + '\n')
        self.tn.write("rm - rf / var / lib / rancher /" + '\n')
        self.tn.write("rm - rf / run / kubernetes /" + '\n')
        self.tn.write("docker volume rm $(docker volume ls - q)" + '\n')

    def get_linux_version(self):
        version=""
        self.tn.write("cat /proc/version"+'\n')
        time.sleep(2)
        data=self.tn.read_very_eager()
        if re.search(r'(centos)',data):
            tmp=re.search(r'Linux version\s*(\d*.\d*.\d*-\d*)',data).group(1)
            self.tn.write("cat /etc/redhat-release" + '\n')
            time.sleep(2)
            v=self.tn.read_very_eager()
            print v
            v_data=re.search(r'release (\d*.\d*.\d*)',v).group(1)
            version= "CentOS "+v_data+" "+tmp

        return version


    def get_docker_version(self):
        self.tn.write('docker version' + '\n')
        time.sleep(3)
        data = self.tn.read_very_eager()
        print data
        if re.search(r'(command not found)',data):
            return 0
        if re.search(r'(Cannot)',data):
            self.tn.write("systemctl start docker" + '\n')
            time.sleep(10)
            self.tn.write('docker version' + '\n')
            time.sleep(1)
            data = self.tn.read_very_eager()
            docker_version = "Client " + re.search(r'Client:\s*(Version:\s*\S*)', data).group(1) + '\t\t\t' + "Server " + re.search(r'Server:\s*(Version:\s*\S*)', data).group(1)
            return docker_version
        docker_version="Client "+re.search(r'Client:\s*(Version:\s*\S*)', data).group(1)+'\t\t\t'+"Server "+re.search(r'Server:\s*(Version:\s*\S*)',data).group(1)
        return docker_version

    def get_all_container_id(self):
        self.tn.write("docker ps" + '\n')
        time.sleep(1)
        data = self.tn.read_very_eager()
        n=0
        data_list=data.split('\n')
        data_list.pop()
        container={}
        for i in  data_list:
            if n>1 :
                container_data=re.findall(r'(\S*)',i)
                while '' in container_data:
                    container_data.remove('')
                container[container_data[1]]=container_data[0]
            n=n+1
        return container

    def get_container_id(self,name):
        all_id=self.get_all_container_id()
        return all_id[name]

    def get_container_ip(self,id):
        self.tn.write("docker inspect "+id+" | grep container.ip"+'\n')
        time.sleep(1)
        data=self.tn.read_very_eager()
        return re.search(r':\s*\"(\w*\.\w*\.\w*\.\w*)',data).group(1)

    def getin_container(self,id):
        cmd="docker exec -it " +id+ " /bin/bash"
        self.tn.write(cmd+'\n')
        time.sleep(2)


    def container_ping(self,container_id,dsp_ip):
        self.getin_container(container_id)
        self.tn.write("ping -c 10 "+dsp_ip+'\n')
        time.sleep(30)
        data=self.tn.read_very_eager()
        self.tn.write("exit"+'\n')
        new_data=data.split('\n')
        return new_data[-3]

    def get_haproxy_config(self,container_id):
        self.getin_container(container_id)
        self.tn.write("cat /etc/haproxy/haproxy.cfg"+'\n')
        time.sleep(3)
        data=self.tn.read_very_eager()
        self.tn.write("exit"+'\n')
        return data

    def install_docker(self,dir,file):
        self.change_root()
        self.tn.write("cd /tmp/"+'\n')
        file_dir=os.path.join(os.getcwd(),dir)
        file=os.path.join(file_dir,file)
        f = open(file, 'r')
        for command in f.readlines():
            if re.search(r'rpm',command):
                cmd="rpm -ivh "+command
            else:
                cmd="yum -y install "+command
            self.tn.write(cmd+'\n')
            time.sleep(10)
        self.tn.write("systemctl daemon-reload"+'\n')
        time.sleep(5)
        self.tn.write("systemctl start docker"+'\n')
        time.sleep(20)
        self.tn.write("curl -sSL https://get.daocloud.io/daotools/set_mirror.sh | sh -s http://fd56d5b4.m.daocloud.io"+'\n')
        time.sleep(5)
        self.tn.write("systemctl restart docker"+'\n')
        time.sleep(20)
        f.close()

    def install_mysql(self,fire_dir='CentOS7.2_docker1.12'):
        print >> self.f,"--Check mysql:"
        try:
            db=MySQLdb.connect(self.host,"cattle","cattle","cattle")
            print >> self.f,"\tmysql has already been installed"
            print "--install mysql is done"
        except:
            local_dir = os.path.join(os.getcwd(), fire_dir)
            from SftpTest import Paramiko_SFTP
            Upload_files = Paramiko_SFTP(self.host)
            Upload_files.put_file(local_dir+"\\mysql-community-release-el7-5.noarch.rpm",'/tmp/mysql-community-release-el7-5.noarch.rpm')
            time.sleep(10)
            self.tn.send_cmd('cd /tmp/'+'\n')
            self.tn.send_cmd('rpm -ivh mysql*.rpm'+'\n')
            time.sleep(10)
            self.tn.send_cmd("yum -y install mysql-community-server"+'\n')
            time.sleep(60)
            self.tn.send_cmd('service mysqld restart')
            time.sleep(20)
            self.tn.send_cmd('systemctl enable mysqld')
            time.sleep(2)
            self.tn.send_cmd('systemctl daemon-reload')
            time.sleep(2)
            db = MySQLdb.connect(self.host)
            cursor = db.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS cattle COLLATE = 'utf8_general_ci' CHARACTER SET = 'utf8';")
            cursor.execute("GRANT ALL ON cattle.* TO 'cattle'@'%' IDENTIFIED BY 'cattle';")
            cursor.execute("GRANT ALL ON cattle.* TO 'cattle'@'localhost' IDENTIFIED BY 'cattle';")
            db.close()
            print >> self.f, "--install mysql is done"
            print "--install mysql is done"

    def centos_pre_install_docker(self,fire_dir):
        print "---install docker on "+self.host
        local_dir =os.path.join(os.getcwd(),fire_dir)
        from SftpTest import Paramiko_SFTP
        Upload_files=Paramiko_SFTP(self.host)
        Upload_files.put_dir_files(local_dir,'/tmp/')
        self.install_docker(fire_dir,fire_dir+'.txt')

    def check_install_docker(self,fire_dir):
        self.change_root()
        sysversion=self.get_linux_version()
        version=self.get_docker_version()
        if version==0:
            print >> self.f,"--need to install docker"
            print "--need to install docker"
            if sysversion.split(' ')[0].lower()=="centos":
                self.centos_pre_install_docker(fire_dir)
        else:
            print >> self.f,"--Chech Docker:"+'\n\t'+version

    def install_rancher(self,version="rancher/server:v1.5.5"):
        id=self.send_cmd("docker ps \n")
        n=0
        while (id !=""):
            try:
                if re.search(r'(rancher)',id).group(1):
                    break
            except:
                cmd="docker run -d --restart=always -p 8080:8080 "+version+" --db-host "+self.host+" --db-port 3306 --db-user cattle --db-pass cattle --db-name cattle"
                print '\t' + self.host + '\t'+cmd
                self.send_cmd(cmd + '\n')
                time.sleep(10)
                id = self.send_cmd("docker ps \n")
                if (n == 20):
                    break
                n = n + 1
                time.sleep(200)
        id_list=id.split('\n')
        id_list.pop()
        id=id_list[-1]
        print "\tRancher Server is up:\t" + id

    def send_cmd(self,cmd):
        self.tn.write(cmd)
        time.sleep(2)
        response=self.tn.read_very_eager()
#        print "response:"+response
        return response

    def close(self):
        self.tn.close()
        print "Telnet:"+self.host+" is closed!"

if __name__ == "__main__":
    testT=RTelnet('112.74.100.4','agent003','liubin198244')
    testT.login()
    testT.change_root()
    if testT.get_linux_version() == "centos":
        pass
    version=testT.get_docker_version()
    if re.search(r'(command not found)',version):
        print "---need to install docker"
        testT.install_docker()
    else:
        print re.search(r'(Client:\s*Version:\s*\S*)',version).group(1)
        print re.search(r'(Server:\s*Version:\s*\S*)',version).group(1)

    testT.close()