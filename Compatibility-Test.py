from RancherServerTest import RancherServer
from TelnetTest import RTelnet
import os,time,re
import MySQLdb

class Setup_env(object):
    def __init__(self,host_ip):
        self.host_ip=host_ip
        self.NewTelnet = RTelnet(host_ip)
        self.NewTelnet.login()

    def centos_pre_install_docker(self,fire_dir):
        print "---install docker on "+self.host_ip
        local_dir =os.path.join(os.getcwd(),fire_dir)
        from SftpTest import Paramiko_SFTP
        Upload_files=Paramiko_SFTP(self.host_ip)
        Upload_files.put_dir_files(local_dir,'/tmp/')
        self.NewTelnet.install_docker(fire_dir,fire_dir+'.txt')


    def install_docker(self,fire_dir):
        self.NewTelnet.change_root()
        sysversion=self.NewTelnet.get_linux_version()
        version=self.NewTelnet.get_docker_version()
        if version==0:
            print "--need to install docker"
            if sysversion.split(' ')[0].lower()=="centos":
                self.centos_pre_install_docker(fire_dir)
        else:
            print "--OS version:"+'\t'+sysversion+"\n--Docker version:"+'\t'+version

    def install_rancher(self,version="rancher/server:v1.5.5"):
        id=self.NewTelnet.send_cmd("docker ps \n")
        n=0
        while (id !=""):
            try:
                if re.search(r'(rancher)',id).group(1):
                    break
            except:
                cmd="docker run -d --restart=always -p 8080:8080 "+version+" --db-host "+self.host_ip+" --db-port 3306 --db-user cattle --db-pass cattle --db-name cattle"
                print '\t' + self.host_ip + '\t'+cmd
                self.NewTelnet.send_cmd(cmd + '\n')
                time.sleep(10)
                id = self.NewTelnet.send_cmd("docker ps \n")
                if (n == 20):
                    break
                n = n + 1
                time.sleep(200)
        id_list=id.split('\n')
        id_list.pop()
        id=id_list[-1]
        print "\tRancher Server is up:\t" + id

    def install_mysql(self,fire_dir='CentOS7.2_docker1.12'):
        print "---install mysql on " + self.host_ip
        try:
            db=MySQLdb.connect(self.host_ip,"cattle","cattle","cattle")
            print "---install mysql is done"
        except:
            local_dir = os.path.join(os.getcwd(), fire_dir)
            from SftpTest import Paramiko_SFTP
            Upload_files = Paramiko_SFTP(self.host_ip)
            Upload_files.put_file(local_dir+"\\mysql-community-release-el7-5.noarch.rpm",'/tmp/mysql-community-release-el7-5.noarch.rpm')
            time.sleep(10)
            self.NewTelnet.send_cmd('cd /tmp/'+'\n')
            self.NewTelnet.send_cmd('rpm -ivh mysql*.rpm'+'\n')
            time.sleep(10)
            self.NewTelnet.send_cmd("yum -y install mysql-community-server"+'\n')
            time.sleep(60)
            self.NewTelnet.send_cmd('service mysqld restart')
            time.sleep(20)
            self.NewTelnet.send_cmd('systemctl enable mysqld')
            time.sleep(2)
            self.NewTelnet.send_cmd('systemctl daemon-reload')
            time.sleep(2)
            db = MySQLdb.connect(self.host_ip)
            cursor = db.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS cattle COLLATE = 'utf8_general_ci' CHARACTER SET = 'utf8';")
            cursor.execute("GRANT ALL ON cattle.* TO 'cattle'@'%' IDENTIFIED BY 'cattle';")
            cursor.execute("GRANT ALL ON cattle.* TO 'cattle'@'localhost' IDENTIFIED BY 'cattle';")
            db.close()


    def close(self):
        self.NewTelnet.close()


if __name__ == "__main__":
    system_os='CentOS7.3'

    if system_os == 'CentOS7.2':
        rancher_server_ip=['120.76.143.97', '10.116.27.222']
        agents_outer_ip = ["120.24.159.214", "120.25.254.32", "120.25.254.221", "120.24.228.201"]
        agents_inner_ip = ["10.169.210.12", "10.116.97.118", "10.116.97.222", "10.170.47.15"]
        file_dir='CentOS7.2_docker1.12'
    if system_os == 'CentOS7.3':
        rancher_server_ip = ['112.74.197.212', '10.45.166.186']
        agents_outer_ip = ["112.74.25.81", "120.25.65.45", "120.25.159.42", "120.76.145.193"]
        agents_inner_ip = ["10.170.47.124", "10.24.146.184", "10.116.141.136", "10.170.18.147"]
        file_dir = 'CentOS7.3_docker1.12'

    rancher_version="rancher/server:v1.6.0-rc3"
    engine="Cattle"
    networking="VXLAN"
    service_name=["LBservice"+engine+networking,"Nginx"+engine+networking,"RabbitMQ"+engine+networking]

    print "Setup Test Env"
    print "-Setup Rancher Server: "+rancher_server_ip[0]
    CentosTest=Setup_env(rancher_server_ip[0])
    CentosTest.install_mysql(file_dir)
    CentosTest.install_docker(file_dir)
    CentosTest.install_rancher(rancher_version)
    CentosTest.close()

    print "-Setup Hosts:"
    for ip in agents_outer_ip:
        print "--setup host: "+ip
        CentosTest=Setup_env(ip)
        CentosTest.install_docker(file_dir)
        CentosTest.close()

    NewTest=RancherServer('http://'+rancher_server_ip[0]+":8080",agents_outer_ip,agents_inner_ip)
    NewTest.login()
    NewTest.set_settings_host('http://' + rancher_server_ip[1] + ":8080")
    NewTest.set_settings_catalog()
    all_env = NewTest.get_all_env()
    if networking=="VXLAN":
        template_admin_name="test_admin_"+engine+"_"+networking
        networking_type_admin="Rancher VXLAN - ADMIN"
        networking_type="Rancher VXLAN - USER"
    else:
        networking_type = "Rancher VXLAN"
    template_name="test_user_"+engine+"_"+networking

    if networking=="VXLAN":
        try:
            env_id = all_env[template_admin_name]
        except:
            print "---add env-template"
            NewTest.add_env_template(template_admin_name, engine, networking_type_admin,"Rancher IPsec")
            print "\t" + template_admin_name
            print "---add env"
            NewTest.add_env(template_admin_name)
            time.sleep(4)
    try:
        env_id=all_env[template_name]
    except:
        print "---add env-template"
        if networking=="VXLAN":
            NewTest.add_env_template(template_name, engine, networking_type,"Rancher IPsec")
        else:
            NewTest.add_env_template(template_name, engine, networking_type)
        print "\t" + template_name
        print "---add env"
        NewTest.add_env(template_name)
        time.sleep(4)

    all_env = NewTest.get_all_env()
    if networking == "VXLAN":
        NewTest.glb_config(all_env[template_admin_name], all_env[template_name])

    print "---Add stack"
    if networking == "VXLAN":
        stack_id=NewTest.get_stack_all_id(all_env[template_admin_name])
        try:
            stack_id["GLB"+engine+networking]
        except:
            NewTest.add_stack(all_env[template_admin_name], "GLB"+engine+networking)
        print "\t"+"GLB"+engine+networking+"\ton ENV:"+template_admin_name
    stack_id=NewTest.get_stack_all_id(all_env[template_name])
    for i in service_name:
        try:
            stack_id[i]
        except:
            NewTest.add_stack(all_env[template_name],i)
        print "\t"+i+"\ton ENV:"+template_name
    print "---Add stack done"

    host_states =NewTest.get_all_host_state(all_env[template_name])
    print "---Add host"
    if networking == "VXLAN":
        admin_host_states = NewTest.get_all_host_state(all_env[template_admin_name])
        if agents_inner_ip[-1] not in admin_host_states.keys():
            NewTest.add_host(all_env[template_admin_name],agents_outer_ip[-1])
        print "\tadd host:"+agents_outer_ip[-1]+" to ENV:"+template_admin_name
        for n in range(0,len(agents_outer_ip)-1):
            ip=agents_inner_ip[n]
            print "\tadd host:" + agents_outer_ip[n] + " to ENV:" + template_name
            if ip in host_states.keys():
                continue
            NewTest.add_host(all_env[template_name], agents_outer_ip[n])
    else:
        for ip in agents_outer_ip:
            index=agents_outer_ip.index(ip)
            print "\tadd host:" + ip + " to ENV:" + template_name
            if agents_inner_ip[index] in host_states.keys():
                continue
            NewTest.add_host(all_env[template_name],ip)
    print "---Add host done"


    if networking == "VXLAN":
        print "---" +template_admin_name+" is being checked"
        admin_host=NewTest.get_host_state(all_env[template_admin_name])
        print "\thosts:"
        for key, vaule in admin_host.items():
            print "\t\t" + str(key) + " : " + vaule
        result = 1
        n = 0
        while (result == 1):
            host_data = NewTest.get_stack_state_all(all_env[template_admin_name])
            result = 0
            for i in host_data.values():
                if i != "Active":
                    result = 1
            n = n + 1
            if n == 20:
                break
        print "\tstack:"
        for key, value in host_data.items():
            print "\t\t" + key + " : " + value
    print "---" + template_name + " is being checked"
    hoststate=NewTest.get_host_state(all_env[template_name])
    print "\thosts:"
    for key, vaule in hoststate.items():
        print "\t\t" + str(key) + " : " + vaule

    result=1
    n=0
    while(result==1):
        data=NewTest.get_stack_state_all(all_env[template_name])
        result=0
        for i in data.values():
            if i != "Active":
                result=1
        n=n+1
        if n==2:
            break
    print "\tstack:"
    for key,value in data.items():
        print "\t\t"+key+" : "+value

    print "---Containers Ping each other is being checked"
    NewTest.container_ping_random()

    print "---GLB Service is being checked"
    if networking =="VXLAN":
        NewTest.glb_check(all_env[template_admin_name],NewTest.get_stack_all_id(all_env[template_admin_name])["GLB"+engine+networking],agents_outer_ip[-1])

    NewTest.close()

