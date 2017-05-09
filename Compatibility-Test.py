from RancherServerTest import RancherServer
from TelnetTest import RTelnet
import os,time,sys

class Compatibility_Test(object):
    def __init__(self,system_os='CentOS7.3',rv='rancher/server:v1.6.0',engine='Cattle',networking='VXLAN'):
        if system_os == 'CentOS7.2':
            self.rancher_server_ip = ['120.76.143.97', '10.116.27.222']
            self.agents_outer_ip = ["120.24.159.214", "120.25.254.32", "120.25.254.221", "120.24.228.201"]
            self.agents_inner_ip = ["10.169.210.12", "10.116.97.118", "10.116.97.222", "10.170.47.15"]
            self.file_dir = 'CentOS7.2_docker1.12'
        if system_os == 'CentOS7.3':
            self.rancher_server_ip = ['112.74.197.212', '10.45.166.186']
            self.agents_outer_ip = ["112.74.25.81", "120.25.65.45", "120.25.159.42", "120.76.145.193"]
            self.agents_inner_ip = ["10.170.47.124", "10.24.146.184", "10.116.141.136", "10.170.18.147"]
            self.file_dir = 'CentOS7.3_docker1.12'
        self.host_ip=self.rancher_server_ip[0]
        self.rancher_version = rv
        self.engine = engine
        self.networking = networking
        self.service_name = ["LBservice" + self.engine + self.networking, "Nginx" + self.engine + self.networking,"RabbitMQ" + self.engine + self.networking]
        self.NewRancherServerTest = ''
        if self.networking == "VXLAN":
            self.template_admin_name = "Test_admin_" + self.engine + "_" + self.networking
            self.networking_type_admin = "Rancher VXLAN - ADMIN"
            self.networking_type = "Rancher VXLAN - USER"
        else:
            self.networking_type = "Rancher "+self.networking
        self.template_name = "Test_user_" + self.engine + "_" + self.networking
        report_time=time.strftime('%Y-%m-%d_%H%M%S',time.localtime(time.time()))
        report_dir = os.path.join(os.getcwd(), 'report')
        if not os.path.exists(report_dir):
            os.mkdir(report_dir)
        report_name="\\Report_"+system_os+"_"+self.engine+"_"+self.networking+"_"+report_time+".log"
        self.f=open(report_dir+report_name,'a')
        print >> self.f,system_os+"_"+self.rancher_version+"_"+self.engine+"_"+self.networking

    def setup_env(self):
        print "Setup Test Env"
        print >> self.f,"\n-Setup RancherServer: " + self.rancher_server_ip[0]
        print "-Setup RancherServer: " + self.rancher_server_ip[0]
        self.NewTelnet = RTelnet(self.host_ip,self.f)
        self.NewTelnet.login()
        print >> self.f, "--Check OSversion: "
        print >> self.f,'\t'+self.NewTelnet.get_linux_version()
        self.NewTelnet.install_mysql(self.file_dir)
        self.NewTelnet.check_install_docker(self.file_dir)
        self.NewTelnet.install_rancher(self.rancher_version)
        self.NewTelnet.close()

        for ip in self.agents_outer_ip:
            print >> self.f,"\n-Setup Host: " + ip
            print "--Setup host: " + ip
            NewHostTest=RTelnet(ip,self.f)
            NewHostTest.login()
            print >> self.f, "--Check OSversion: "
            print >> self.f,'\t'+NewHostTest.get_linux_version()
            NewHostTest.check_install_docker(self.file_dir)
            NewHostTest.close()

    def config_rancher_server(self):
        self.NewRancherServerTest = RancherServer('http://' + self.rancher_server_ip[0] + ":8080", self.agents_outer_ip,self.agents_inner_ip,self.f)
        self.NewRancherServerTest.login()
        self.NewRancherServerTest.set_settings_host('http://' + self.rancher_server_ip[1] + ":8080")
        self.NewRancherServerTest.set_settings_catalog()
        all_env = self.NewRancherServerTest.get_all_env()
        print >> self.f, "---Delete hosts"
        print "---Delete hosts"
        for id in all_env.values():
            for ip in self.agents_inner_ip:
                self.NewRancherServerTest.delete_all_host(id)
        print >> self.f, "---Add env-template"
        if self.networking == "VXLAN":
            if self.template_admin_name not in all_env.keys():
                print "---add env-template"
                self.NewRancherServerTest.add_env_template(self.template_admin_name, self.engine, self.networking_type_admin)
                print >> self.f,"\t" + self.template_admin_name
                print "\t" + self.template_admin_name
                print >> self.f,"---Add env"
                print "---add env"
                self.NewRancherServerTest.add_env(self.template_admin_name)
                time.sleep(4)
            print >> self.f, "\t"+self.template_admin_name
        if self.template_name not in all_env.keys():
            print >> self.f,"---Add env-template"
            print "---add env-template"
            self.NewRancherServerTest.add_env_template(self.template_name, self.engine, self.networking_type)
            print >> self.f,"\t" + self.template_name
            print "\t" + self.template_name
            print >> self.f,"---Add env"
            print "---add env"
            self.NewRancherServerTest.add_env(self.template_name)
            time.sleep(4)
        print >> self.f, "\t" + self.template_name

        all_env = self.NewRancherServerTest.get_all_env()
        if self.networking == "VXLAN":
            self.NewRancherServerTest.glb_config(all_env[self.template_admin_name], all_env[self.template_name])

        print >> self.f,"---Add Stack"
        print "---Add stack"
        if self.networking == "VXLAN":
            stack_id = self.NewRancherServerTest.get_stack_all_id(all_env[self.template_admin_name])
            try:
                stack_id["GLB" + self.engine + self.networking]
            except:
                self.NewRancherServerTest.add_stack(all_env[self.template_admin_name], "GLB" + self.engine + self.networking)
            print >> self.f,"\t" + "GLB" + self.engine + self.networking + "\ton ENV:" + self.template_admin_name
            print "\t" + "GLB" + self.engine + self.networking + "\ton ENV:" + self.template_admin_name
        stack_id = self.NewRancherServerTest.get_stack_all_id(all_env[self.template_name])
        for i in self.service_name:
            try:
                stack_id[i]
            except:
                self.NewRancherServerTest.add_stack(all_env[self.template_name], i)
            print >> self.f,"\t" + i + "\ton ENV:" + self.template_name
            print "\t" + i + "\ton ENV:" + self.template_name

        host_states = self.NewRancherServerTest.get_all_host_state(all_env[self.template_name])
        print >> self.f,"---Add host"
        print "---Add host"
        if self.networking == "VXLAN":
            admin_host_states = self.NewRancherServerTest.get_all_host_state(all_env[self.template_admin_name])
            if self.agents_inner_ip[-1] not in admin_host_states.keys():
                self.NewRancherServerTest.add_host(all_env[self.template_admin_name], self.agents_outer_ip[-1])
            print >> self.f,"\tadd host:" + self.agents_outer_ip[-1] + " to ENV:" + self.template_admin_name
            print "\tadd host:" + self.agents_outer_ip[-1] + " to ENV:" + self.template_admin_name
            for n in range(0, len(self.agents_outer_ip) - 1):
                ip = self.agents_inner_ip[n]
                print >> self.f,"\tadd host:" + self.agents_outer_ip[n] + " to ENV:" + self.template_name
                print "\tadd host:" + self.agents_outer_ip[n] + " to ENV:" + self.template_name
                if ip in host_states.keys():
                    continue
                self.NewRancherServerTest.add_host(all_env[self.template_name], self.agents_outer_ip[n])
        else:
            for ip in self.agents_outer_ip:
                index = self.agents_outer_ip.index(ip)
                print >> self.f,"\tadd host:" + ip + " to ENV:" + self.template_name
                print "\tadd host:" + ip + " to ENV:" + self.template_name
                if self.agents_inner_ip[index] in host_states.keys():
                    continue
                self.NewRancherServerTest.add_host(all_env[self.template_name], ip)
        self.NewRancherServerTest.get_all_host_ip(all_env[self.template_name])
        print "---Add host done"

    def states_check(self):
        all_env = self.NewRancherServerTest.get_all_env()
        if self.networking == "VXLAN":
            print >> self.f,"---" + self.template_admin_name + " Check"
            print "---" + self.template_admin_name + " is being checked"
            admin_host = self.NewRancherServerTest.get_host_state(all_env[self.template_admin_name])
            print >> self.f,"\thosts:"
            print "\thosts:"
            for key, vaule in admin_host.items():
                print >> self.f,"\t\t" + str(key) + " : " + vaule
                print "\t\t" + str(key) + " : " + vaule
            result = 1
            n = 0
            while (result == 1):
                host_data = self.NewRancherServerTest.get_stack_state_all(all_env[self.template_admin_name])
                result = 0
                for i in host_data.values():
                    if i != "Active":
                        result = 1
                n = n + 1
                if n == 20:
                    break
            print >> self.f, "\tstack:"
            print "\tstack:"
            for key, value in host_data.items():
                print >> self.f,"\t\t" + key + " : " + value
                print "\t\t" + key + " : " + value
        print >> self.f,"---" + self.template_name + " Checked"
        print "---" + self.template_name + " is being checked"
        hoststate = self.NewRancherServerTest.get_host_state(all_env[self.template_name])
        print >> self.f,"\thosts:"
        print "\thosts:"
        for key, vaule in hoststate.items():
            print >> self.f,"\t\t" + str(key) + " : " + vaule
            print "\t\t" + str(key) + " : " + vaule

        result = 1
        n = 0
        while (result == 1):
            data = self.NewRancherServerTest.get_stack_state_all(all_env[self.template_name])
            result = 0
            for i in data.values():
                if i != "Active":
                    result = 1
            n = n + 1
            if n == 20:
                break
        print >> self.f,"\tstack:"
        print "\tstack:"
        for key, value in data.items():
            print >> self.f,"\t\t" + key + " : " + value
            print "\t\t" + key + " : " + value

    def container_ping_random(self):
        print >> self.f,"---Check Containers Ping"
        print "---Containers Ping each other is being checked"
        self.NewRancherServerTest.container_ping_random()

    def glb_check(self):
        print >> self.f,"---Check GLB Service"
        print "---GLB Service is being checked"
        all_env = self.NewRancherServerTest.get_all_env()
        stack_id=self.NewRancherServerTest.get_stack_all_id(all_env[self.template_admin_name])["GLB" + self.engine + self.networking]
        if self.networking == "VXLAN":
            self.NewRancherServerTest.glb_check(all_env[self.template_admin_name],stack_id,self.agents_outer_ip[-1])

    def close(self):
        self.NewRancherServerTest.close()
        self.f.close()


if __name__ == "__main__":
    osversion=['CentOS7.3','CentOS7.2']
    rancher_server='rancher/server:v1.6.0'
    engine=['Cattle']
    networking=['IPsec','VXLAN']

    osversion = ['CentOS7.3']
    engine = ['Kubernetes']
    networking = ['IPsec']

    for v in osversion:
        for e in engine:
            for nw in networking:
                NewTest=Compatibility_Test(v,rancher_server,e,nw)
                NewTest.setup_env()
                NewTest.config_rancher_server()
                NewTest.states_check()
                NewTest.container_ping_random()
                if nw=="VXLAN" and engine=="Cattle":
                    NewTest.glb_check()
                NewTest.close()


