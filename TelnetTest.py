#encoding=utf-8
import telnetlib
import time,re,os

class RTelnet(object):
    def __init__(self,host):
        self.host=host
        self.port="23"
        self.username='agent'
        self.userpasswd='test'
        self.tn = telnetlib.Telnet(self.host, self.port, timeout=10)

    def login(self):
#        print "----login begin"
        self.tn=telnetlib.Telnet(self.host,self.port,timeout=10)
        self.tn.set_debuglevel(2)
        self.tn.read_until('login:')
        self.tn.write(self.username+'\n')
        self.tn.read_until('Password:')
        self.tn.write(self.userpasswd+'\n')
        self.tn.read_until('$')
#        print "----login sucess"

    def change_root(self):
        self.tn.write("su" + '\n')
        time.sleep(.4)
        data = self.tn.read_very_eager()
        if re.search(r'(command not found)', data):
            pass
        else:
            self.tn.write("XLuo+Agi198244" + '\n')
            time.sleep(1)

    def get_linux_version(self):
        self.tn.write("cat /proc/version"+'\n')
        time.sleep(.4)
        data=self.tn.read_very_eager()
        try:
            if re.search(r'(centos)',data).group(1)=="centos":
                tmp=re.search(r'Linux version\s*(\d*.\d*.\d*-\d*)',data).group(1)
                version= "CentOS "+tmp
        except:
            version=None
        return version


    def get_docker_version(self):
        self.tn.write('docker version' + '\n')
        time.sleep(1)
        data = self.tn.read_very_eager()
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
        return data

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

    def send_cmd(self,cmd):
        self.tn.write(cmd)
        time.sleep(1)
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