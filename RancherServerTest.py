#!usr/bin/python
#coding=utf-8
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time,re,random,os,SendKeys,sys

class RancherServer(object):
    def __init__(self,rancherserver_url,agents_outer_ip,agents_inner_ip,report_file):
        self.rancherserver_ip = rancherserver_url
        self.rancherserver_username = "bin"
        self.rancherserver_passwd = "1234"
        self.agents_outer_ip = agents_outer_ip
        self.agents_inner_ip = agents_inner_ip
        self.agent_username = "agent"
        self.agent_userpasswd = "test"
        self.root_passwd = "XLuo+agi198244"
        self.glb_env_name="admin-cattle-vxlan"
        self.f=report_file

    def login(self):
#        self.dr = webdriver.Firefox()
        self.dr=webdriver.Chrome()
        print >> self.f,"\n-Rancher Server is open! "+self.rancherserver_ip
        self.dr.get(self.rancherserver_ip)
        self.dr.implicitly_wait(5)
        self.dr.find_element_by_xpath("//button")
        try:
            self.dr.find_element_by_class_name("farm-box")
            time.sleep(1)
            self.dr.find_element_by_class_name("login-user").send_keys(self.rancherserver_username)
            self.dr.find_element_by_class_name("login-pass").send_keys(self.rancherserver_passwd)
            self.dr.find_element_by_xpath("//button").click()
            time.sleep(1)
            for cookie in self.dr.get_cookies():
                self.dr.add_cookie({'name': cookie['name'], 'value': cookie['value']})
            time.sleep(1)
            print >> self.f,"--Rancher Server Login is successful"
            return
        except:
            try:
                time.sleep(2)
                self.dr.find_element_by_class_name("footer-actions").click()
                self.dr.find_element_by_xpath("//div[@class='footer-actions']/button").click()
                time.sleep(2)
            except:
                self.dr.get(self.rancherserver_ip+"/admin/access/local")
                time.sleep(2)
                self.dr.implicitly_wait(5)
                self.dr.find_element_by_class_name("clearfix")
                self.dr.find_element_by_xpath('//section[@class="well"]/div[@class="row"]/div[@class="col-md-6"]/div[@class="form-group"]/input[1]').send_keys("bin")
                self.dr.find_element_by_xpath('//section[@class="well"]/div[2]/div[1]/div[@class="form-group"]/input').send_keys("1234")
                self.dr.find_element_by_xpath('//section[@class="well"]/div[2]/div[2]/div[@class="form-group"]/input').send_keys("1234")
                self.dr.find_element_by_xpath("//button[@class='btn btn-primary']").click()
                print "----add local user-----"
                time.sleep(10)


    def close(self):
        self.dr.close()
        self.dr.quit()
        print "-Browser is closed!"

    def get_env_id(self, env_name='testENV'):
        self.dr.get(self.rancherserver_ip + "/v2-beta/projects?all=true&limit=-1&sort=name")
#        print "------getting environment: "+ENV_name+" id------"
        data = re.search(r'"data"\:\[(\S*)]', self.dr.page_source).group(1)
        data_id=re.findall(r'"id"\:\"(\w*)\"',data)
        data_name=re.findall(r'"name"\:\"(\w*)\"',data)
        i=0
        for i in range(len(data_name)):
            if data_name[i] == env_name:
#                print "------environment "+ENV_name+" id="+data_id[i]
                return data_id[i]

    def get_all_env(self):
        self.dr.get(self.rancherserver_ip + "/v2-beta/projects?all=true&limit=-1&sort=name")
        data = re.search(r'"data"\:\[(\S*)]', self.dr.page_source).group(1)
        all_id=re.findall(r'"id"\:\s*\"(\w*)\"',data)
        all_name= re.findall(r'"name"\:\s*\"([\w\-]*)\"', data)
        all_env={}
        n=0
        for name in all_name:
            all_env[name]=all_id[n]
            n=n+1
        return all_env

    def add_env(self,env_template_name='New'):
        self.dr.get(self.rancherserver_ip + "/settings/env/add")
        time.sleep(2)
        self.dr.implicitly_wait(25)
        self.dr.find_element_by_class_name("clearfix")
        time.sleep(1)
        self.dr.find_element_by_class_name("ember-text-field").send_keys(env_template_name)
        expr='//section[@class="well"]/div/div/div/a/div[text()="'+env_template_name+'"]/..'
        self.dr.find_element_by_xpath(expr).click()
        self.dr.find_element_by_xpath("//div[@class='ember-view footer-actions']/button[@class='btn btn-primary']").click()
        print "\t" + env_template_name
        return env_template_name

    def set_env_template(self):
        pass

    def add_env_template(self,name,engine_type='Cattle',networking_type='IPsec'):
        type=networking_type
        self.dr.get(self.rancherserver_ip+"/settings/env/add-template")
        self.dr.implicitly_wait(15)
        self.dr.find_element_by_class_name("clearfix")
        time.sleep(2)
        self.dr.find_element_by_xpath("//section[@class='well r-mb0']/div[@class='ember-view']/div[@class='row form-group']"
                                      "/div/input").send_keys(name)
        element = "//section[@class='well r-mb0']/div[@class='row']/div/div/a[@title='" + engine_type + "']"
        engine_elements = self.dr.find_elements_by_xpath(element)
        if len(engine_elements)>1:
            if engine_type=="Kubernetes":
                for i in engine_elements:
                    if i.find_element_by_xpath("./div[2]").text=="in K8s":
                        i.click()
            else:
                for i in engine_elements:
                    if i.find_element_by_xpath("./div[2]").text == "in Library":
                        i.click()
        else:
            self.dr.find_element_by_xpath(element).click()
        time.sleep(1)
        js = "var q=document.documentElement.scrollTop=500"
        self.dr.execute_script(js)
        element=self.dr.find_element_by_xpath('//section/h4[text()="Networking"]/..')
        num=0
        try:
            active_elements=self.dr.find_elements_by_xpath('//section/h4[text()="Networking"]/../div/div[@class="ember-view catalog-box"]')
            num = len(active_elements)
        except:
            pass
        if num >0:
            for i in active_elements:
#                print i.find_element_by_xpath('./div[@class="itemwrap"]/h5').text,i.find_element_by_xpath('./div[@class="itemwrap"]/span/span').text
                if i.find_element_by_xpath('./div[@class="itemwrap"]/h5').text == type:
                    if engine_type == "Kubernetes":
                        if i.find_element_by_xpath('./div[@class="itemwrap"]/span/span').text != "K8s":
                            i.find_element_by_xpath("//div[@class='footer']/button[2]").click()
                    else:
                        if i.find_element_by_xpath('./div[@class="itemwrap"]/span/span').text != "Library":
                            i.find_element_by_xpath("./div[@class='footer']/button[2]").click()
                else:
                    i.find_element_by_xpath("./div[@class='footer']/button[2]").click()
                time.sleep(1)
        num=0
        try:
            inactive_elements=self.dr.find_elements_by_xpath('//section/h4[text()="Networking"]/../div/div[@class="ember-view catalog-box inactive"]')
            num = len(inactive_elements)
        except:
            pass
        if num>0:
            for i in inactive_elements:
                if_click=0
#                print i.find_element_by_xpath('./div[@class="itemwrap"]/h5').text,i.find_element_by_xpath('./div[@class="itemwrap"]/span/span').text
                if i.find_element_by_xpath('./div[@class="itemwrap"]/h5').text == type:
                    if engine_type == "Kubernetes" and i.find_element_by_xpath('./div[@class="itemwrap"]/span/span').text == "K8s":
                        i.find_element_by_xpath("./div[@class='footer']/button").click()
                        if_click=1
                    if engine_type != "Kubernetes" and i.find_element_by_xpath('./div[@class="itemwrap"]/span/span').text == "Library":
                        i.find_element_by_xpath("./div[@class='footer']/button").click()
                        if_click=1
                    if engine_type != "Kubernetes" and i.find_element_by_xpath('./div[@class="itemwrap"]/span/span').text == "Myvxlan":
                        i.find_element_by_xpath("./div[@class='footer']/button").click()
                        if_click=1
                    if if_click>0:
                        time.sleep(1)
                        js = "var q=document.documentElement.scrollTop=500"
                        self.dr.execute_script(js)
                        time.sleep(1)
                        self.dr.find_element_by_xpath(
                            "//body[@class='no-touch ember-application theme-ui-light']/div[@class='ember-view']")
                        self.dr.find_element_by_xpath("//div[@class='ember-view lacsso modal-overlay modal-open']/div"
                                                      "/div/div[@class='footer-actions']/div/button[@class='btn btn-primary']").click()
                        time.sleep(1)
        self.dr.find_element_by_xpath("//main[@class='clearfix']/div[@class='ember-view']/div[@class='ember-view footer-actions']"
                                      "/button[@class='btn btn-primary']").click()
        time.sleep(5)
        return name

    def glb_config(self,env_id,user_env_id):
        print >> self.f,"---Set GLB config"
        print "---GLB config"
        self.dr.get(self.rancherserver_ip + "/v2-beta/accounts/"+env_id)
        time.sleep(2)
        self.dr.find_element_by_xpath("//div[@id='operations']/button[3]").click()
        time.sleep(1)
        print >> self.f, "\tset allowSystemRole true"
        button_value =self.dr.find_element_by_xpath("//div[@id='request-input']/table/tbody/tr[20]/td[3]/input").is_selected()
        if button_value is not True:
            self.dr.find_element_by_xpath("//div[@id='request-input']/table/tbody/tr[20]/td[3]/input").click()
        self.dr.find_element_by_xpath("//div[@id='request-input']/table/tbody/tr[25]/td[3]/a/i").click()
        time.sleep(1)
        expr="//div[@id='request-input']/table/tbody/tr[25]/td[3]/div[@class='dualValue']/select/option[@value='"+user_env_id+"']"
        self.dr.find_element_by_xpath(expr).click()
        print >> self.f, "\tset projectLinks"
        self.dr.find_element_by_xpath("//body/div[4]/div/div/div[3]/button[1]").click()
        time.sleep(1)
        self.dr.find_element_by_xpath("//body/div[4]/div/div/div[3]/button[1]").click()
        time.sleep(1)
        self.dr.find_element_by_xpath("//body/div[4]/div/div/div[3]/button[2]").click()
#        print >> self.f, "---Set GLB config is done"
        print "---GLB config done"


    def add_stack(self, env_id,Stack_name):
        url = self.rancherserver_ip+"/env/" + env_id + "/apps/stacks/add"
        self.dr.get(url)
        self.dr.implicitly_wait(25)
        self.dr.find_element_by_class_name("clearfix")
        time.sleep(1)
        self.dr.find_element_by_class_name("ember-text-field").send_keys(Stack_name)
        self.dr.find_element_by_class_name("ember-text-area").send_keys("test")
        file_dir=Stack_name
        ABSPATH = os.path.abspath(sys.argv[0])
        path=os.path.join(os.getcwd(),file_dir)
        for file in os.listdir(path):
            if file=="docker-compose.yml":
                docker_yml = os.path.dirname(ABSPATH) + "\\" + file_dir + "\\" + file
            else:
                rancher_yml = "rancher-compose.yml"
        self.dr.find_element_by_xpath("//textarea[@placeholder='Contents of docker-compose.yml']/../span/div/button").click()
        time.sleep(2)
        SendKeys.SendKeys(docker_yml)
        SendKeys.SendKeys("{ENTER}")
        time.sleep(1)
        self.dr.find_element_by_xpath("//textarea[@placeholder='Contents of rancher-compose.yml']/../span/div/button").click()
        time.sleep(1)
        SendKeys.SendKeys(rancher_yml)
        SendKeys.SendKeys("{ENTER}")
        time.sleep(1)
        self.dr.find_element_by_xpath("//div[@class='ember-view footer-actions']/button[@class='btn btn-primary']").click()

    def get_stack_id(self,env_id,stack_name):
        url=self.rancherserver_ip + "/v2-beta/projects/"+str(env_id)+"/stacks/"
        self.dr.get(url)
        print "------getting stack "+stack_name+" id------"
        data_id = re.findall(r'"id"\:\"(\w*)\"', self.dr.page_source)
        data_name = re.findall(r'"name"\:\"(\w*)\"',self.dr.page_source)
        i = 0
        for i in range(len(data_name)):
            if data_name[i] == stack_name:
                print "------stack " + stack_name + " id=" + data_id[i+1]
                return data_id[i+1]

    def get_stack_all_id(self,env_id):
        url = self.rancherserver_ip + "/v2-beta/projects/" + str(env_id) + "/stacks/"
        self.dr.get(url)
#        print "------getting all stack id------"
        data_id = re.findall(r'"id"\:\"(\w*)\"', self.dr.page_source)
        data_name = re.findall(r'"name"\:\"([\w\-]*)\"', self.dr.page_source)
        i = 0
        data={}
        for i in range(len(data_name)):
            data[data_name[i]]=data_id[i]
        return data

    def get_stack_state(self,env_id,stack_id):
        print "------getting stack  state------"
        url=self.RS_ip+"/env/"+str(env_id)+"/apps/stacks/"+str(stack_id)+"?which=all"
        self.dr.get(url)
        self.dr.implicitly_wait(25)
        self.dr.find_element_by_class_name("clearfix")
        time.sleep(4)
        actionItems = self.dr.find_elements_by_xpath("//div[@class='ember-view stack-section r-mt20']/div/div/div/table/tbody/tr")
        data={}
        for id in actionItems:
            print id.text.split(' ')[1]+" : "+id.text.split(' ')[0]
            data[id.text.split(' ')[1]]=id.text.split(' ')[0]
        return data

    def get_stack_state_all(self,env_id):
#        print "------getting all stack state------"
        url = self.rancherserver_ip + "/env/" + str(env_id) + "/apps/stacks?which=all"
        self.dr.get(url)
        self.dr.implicitly_wait(15)
        self.dr.find_element_by_class_name("clearfix")
        time.sleep(1)
        actionItems=self.dr.find_elements_by_xpath("//a[@class='btn btn-link']/i[@class='icon icon-plus']")
        for i in actionItems:
            i.click()
            time.sleep(1)
        actionItems=self.dr.find_elements_by_xpath("//main[@class='clearfix']/section[2]/div/div")
        n=1
        final_data={}
        for i in actionItems:
            repx="//main[@class='clearfix']/section[2]/div/div["+str(n)+"]/div[2]/div/div/table/tbody/tr"
            print >>self.f,'\tstack:'+self.dr.find_element_by_xpath("//main[@class='clearfix']/section[2]/div/div["+str(n)+"]/div[1]/div[3]/h4/a").text
            print '\t\t'+self.dr.find_element_by_xpath("//main[@class='clearfix']/section[2]/div/div["+str(n)+"]/div[1]/div[3]/h4/a").text
            newitems=self.dr.find_elements_by_xpath(repx)
            num=1
            for m in newitems:
                new_repx=repx+"["+str(num)+"]"
                data=self.dr.find_element_by_xpath(new_repx).text
                final_data[data.split(' ')[1]]=data.split(' ')[0]
                print >>self.f,'\t\t'+data.split(' ')[1]+" : "+data.split(' ')[0]
                print '\t\t\t'+data.split(' ')[1]+" : "+data.split(' ')[0]
                num=num+1
            n=n+1
        return final_data

    def add_host(self,env_id,host_ip):
        url = self.rancherserver_ip + "/env/" + str(env_id) + "/infra/hosts/add?driver=custom"
        self.dr.get(url)
        self.dr.implicitly_wait(25)
        self.dr.find_element_by_class_name("clearfix")
        time.sleep(1)
        text=self.dr.find_element_by_xpath("//div[@class='copy-pre']/pre").text
#        print >> self.f,"\tadd host:"+host_ip+"\tcommand:"+text
        print "\tadd host:"+host_ip+"\tcommand:"+text

        from TelnetTest import RTelnet
        telnet_host=RTelnet(host_ip,self.f)
        telnet_host.login()
        telnet_host.change_root()
        telnet_host.send_cmd(str(text)+'\n')
        time.sleep(1)
        self.dr.find_element_by_xpath("//div[@class='footer-actions']/button").click()
        time.sleep(100)
        telnet_host.close()

    def get_host_id(self,ENV_name,Host_ip):
        id = self.get_ENV_id(ENV_name)
        self.dr.get(self.RS_ip + "/v2-beta/projects/"+id+"/hosts")
        time.sleep(1)
        print "------get host "+Host_ip+" id------"
        data = re.search(r'"data":\[\{([\S\s]*)"createDefaults', self.dr.page_source).group(1)
        data_id=re.findall(r'"id"\:\"(\w*)\"',data)
        data_name=re.findall(r'"agentIpAddress"\:\"([\d\.]*)"',data)
        print data_name
        i=0
        for i in range(len(data_name)):
            if data_name[i] == Host_ip:
                print "------get host "+Host_ip+" id="+data_id[i]
                return data_id[i]

    def get_all_host_ip(self,env_id):
        url = self.rancherserver_ip + "/env/" + str(env_id) + "/infra/hosts"
        self.dr.get(url)
        self.dr.implicitly_wait(5)
        self.dr.find_element_by_class_name("clearfix")
        time.sleep(1)
        all_host_ip=[]
        hostip_elements = self.dr.find_elements_by_xpath("//div[@class='pod-info']")
        for ip in hostip_elements:
            all_host_ip.append(ip.text)
        return all_host_ip

    def deactivate_host(self,env_id,host_ip):
        url = self.rancherserver_ip + "/env/" + env_id + "/infra/hosts"
        self.dr.get(url)
        self.dr.implicitly_wait(10)
        self.dr.find_element_by_class_name("clearfix")
        time.sleep(1)
        try:
            actionItems = self.dr.find_elements_by_xpath("//section[@class='ember-view pods clearfix']/div[@class='pod-column']")
            if type(host_ip) is str:
                for n in range(1,len(actionItems)+1):
                    text_repr="//section[@class='ember-view pods clearfix']/div["+str(n)+"]/div[1]/div[3]/div[1]/div[1]"
                    if self.dr.find_element_by_xpath(text_repr).text == host_ip:
                        print "\tdeactivate:" + host_ip
                        repr="//section[@class='ember-view pods clearfix']/div["+str(n)+"]/div[1]/div[1]/div[1]/span"
                        if self.dr.find_element_by_xpath(repr).text != "ACTIVE":
                            continue
                        click_repr="//section[@class='ember-view pods clearfix']/div["+str(n)+"]/div/div[1]/div[2]/div[1]/button[2]"
                        self.dr.find_element_by_xpath(click_repr).click()
                        actionItem = self.dr.find_element_by_xpath("//div[@id='resource-actions-parent']/ul[@id='resource-actions']/li/a[@class='ember-view']")
                        if actionItem.text == "Deactivate":
                            actionItem.click()
            if type(host_ip) is  list:
                for n in range(1,len(actionItems)+1):
                    for ip in host_ip:
                        text_repr = "//section[@class='ember-view pods clearfix']/div[" + str(n) + "]/div[1]/div[3]/div[1]/div[1]"
                        if self.dr.find_element_by_xpath(text_repr).text == ip:
                            print "\tdeactivate:" + ip
                            click_repr = "//section[@class='ember-view pods clearfix']/div[" + str(n) + "]/div/div[1]/div[2]/div[1]/button[2]"
                            self.dr.find_element_by_xpath(click_repr).click()
                            actionItem = self.dr.find_element_by_xpath("//div[@id='resource-actions-parent']/ul[@id='resource-actions']/li/a[@class='ember-view']")
                            if actionItem.text == "Deactivate":
                                actionItem.click()

        except:
            return

    def activate_host(self,ENV_name,Host_ip):
        print "------activate "+Host_ip+"------"
        id = self.get_ENV_id(ENV_name)
        time.sleep(2)
        url = self.RS_ip + "/env/" + str(id) + "/infra/hosts"
        self.dr.get(url)
        self.dr.implicitly_wait(25)
        self.dr.find_element_by_class_name("clearfix")
        time.sleep(1)
        self.dr.find_element_by_xpath("//div[@class='pull-right']/div"
                                      "/button[@data-toggle='dropdown']").click()
        actionItem=self.dr.find_element_by_xpath("//div[@id='resource-actions-parent']"
                                            "/ul[@id='resource-actions']/li/a[@class='ember-view']")
        if actionItem.text == "Activate":
            actionItem.click()
            print "-------activate "+Host_ip+" done"

    def delete_host(self,env_id,host_ip):
        url = self.rancherserver_ip + "/env/" + env_id + "/infra/hosts"
        self.dr.get(url)
        self.dr.implicitly_wait(10)
        self.dr.find_element_by_class_name("clearfix")
        time.sleep(1)
        if re.search(r'(text-center text-muted)',self.dr.page_source):
            return False
        actionItems = self.dr.find_elements_by_xpath("//section[@class='ember-view pods clearfix']/div[@class='pod-column']/div[@class='ember-view pod host']")
        for n in range(1,len(actionItems)+1):
            text_repr = "//section[@class='ember-view pods clearfix']/div[" + str(n) + "]/div[1]/div[3]/div[1]/div[1]"
            if self.dr.find_element_by_xpath(text_repr).text == host_ip:
                print "\tdelete:" + host_ip
                repr = "//section[@class='ember-view pods clearfix']/div[" + str(n) + "]/div[1]/div[1]/div[1]/span"
                click_repr = "//section[@class='ember-view pods clearfix']/div[" + str(n) + "]/div/div[1]/div[2]/div[1]/button[2]"
                self.dr.find_element_by_xpath(click_repr).click()
                actionItem = self.dr.find_element_by_xpath("//div[@id='resource-actions-parent']/ul[@id='resource-actions']/li/a[@class='ember-view']")
                if actionItem.text == "Deactivate":
                    actionItem.click()
                    time.sleep(2)
                self.dr.find_element_by_xpath("//div[@class='pull-right']/div/button[@data-toggle='dropdown']").click()
                time.sleep(2)
                actionItems = self.dr.find_elements_by_xpath("//div[@id='resource-actions-parent']/ul[@id='resource-actions']/li/a[@class='ember-view']")
                for i in actionItems:
                    if i.text == "Delete":
                        i.click()
                        time.sleep(1)
                        self.dr.find_element_by_class_name("btn-danger").click()
                        print "\tdelete " + host_ip + " is done"
                        break
                time.sleep(2)

    def delete_all_host(self, env_id):
        while True:
            url = self.rancherserver_ip + "/env/" + env_id + "/infra/hosts"
            self.dr.get(url)
            self.dr.implicitly_wait(25)
            self.dr.find_element_by_class_name("clearfix")
            time.sleep(1)
            data=self.dr.page_source
            if re.search(r'(No hosts)', data) is not None:
                break
            try:
                text_repr = "//section[@class='ember-view pods clearfix']/div[1]/div[1]/div[3]/div[1]/div[1]"
                print >> self.f,"\tdelete:" + self.dr.find_element_by_xpath(text_repr).text
                print "\tdelete:" + self.dr.find_element_by_xpath(text_repr).text
                click_repr = "//section[@class='ember-view pods clearfix']/div[1]/div/div[1]/div[2]/div[1]/button[2]"
                self.dr.find_element_by_xpath(click_repr).click()
                actionItem = self.dr.find_element_by_xpath("//div[@id='resource-actions-parent']/ul[@id='resource-actions']/li/a[@class='ember-view']")
                if actionItem.text == "Deactivate":
                    actionItem.click()
                    time.sleep(5)
                self.dr.find_element_by_xpath("//div[@class='pull-right']/div/button[@data-toggle='dropdown']").click()
                time.sleep(2)
                actionItems = self.dr.find_elements_by_xpath("//div[@id='resource-actions-parent']/ul[@id='resource-actions']/li/a[@class='ember-view']")
                for i in actionItems:
                    if i.text == "Delete":
                        i.click()
                        time.sleep(1)
                        self.dr.find_element_by_class_name("btn-danger").click()
                        break
                time.sleep(5)
            except:
                pass

    def get_host_state(self,env_id):
#        print "------get " + Host_ip + " state------"
        url = self.rancherserver_ip + "/env/" + str(env_id) + "/infra/hosts"
        self.dr.get(url)
        self.dr.implicitly_wait(25)
        self.dr.find_element_by_class_name("clearfix")
        time.sleep(1)
        hoststate={}
        hoststates_elements = self.dr.find_elements_by_xpath("//div[@class='pod-header clearfix']")
        try:
            hostip_elements= self.dr.find_elements_by_xpath("//div[@class='pod-info']")
            hoststates=[]
            hostip=[]
            for i in hoststates_elements:
                hoststates.append(i.text)
            for i in hostip_elements:
                hostip.append(re.search(r'(\d+.\d+.\d+.\d+)',i.text).group(1))
            n=0
            for i in hostip:
                hoststate[i]=hoststates[n]
                n=n+1
            return hoststate
        except:
            return hoststate

    def get_all_host_state(self,env_id):
        self.dr.get(self.rancherserver_ip + "/v2-beta/projects/"+env_id+"/hosts")
        data=self.dr.page_source
        all_ip = re.findall(r'"agentIpAddress"\:\s*\"(\d*.\d*.\d*.\d*)\"', data)
        all_state = re.findall(r'"name"\s*:\s*\w*,\"state\":\s*"(\w*)"', data)
        result = {}
        n = 0
        for ip in all_ip:
            result[ip] = all_state[n]
            n = n + 1
        return result

    def set_settings_host(self,url):
        print >> self.f,"---Set Host Registration URL"
        print "---Set Host Registration URL"
        self.dr.get(self.rancherserver_ip + "/admin/settings")
        self.dr.implicitly_wait(25)
        self.dr.find_element_by_class_name("clearfix")
        time.sleep(1)
        self.dr.find_element_by_xpath("//div[@class='r-mt10']/label").click()
        text=self.dr.find_element_by_xpath("//div[@class='r-mt10']/input").get_attribute('value')
        if (text == "") or (text==None):
            self.dr.find_element_by_xpath("//div[@class='r-mt10']/input").send_keys(Keys.CONTROL + "a")
            self.dr.find_element_by_xpath("//div[@class='r-mt10']/input").send_keys(url)
            self.dr.find_element_by_xpath("//main[@class='clearfix']/section[2]/div/div[@class='ember-view footer-actions']/button").click()
        else:
            print >> self.f,"\t"+text
            print "\t"+text
        print "---Set Host Registration URL done"

    def get_settings_host(self):
        self.dr.get(self.RS_ip+"/admin/settings")
        self.dr.implicitly_wait(25)
        self.dr.find_element_by_class_name("clearfix")
        time.sleep(1)
        return self.dr.find_element_by_xpath("//div[@class='r-mt10']/input").get_attribute('value')

    def set_settings_catalog(self):
        print >> self.f,"---Set Catalog"
        print "---Set Catalog"
        self.dr.get(self.rancherserver_ip + "/admin/settings")
        self.dr.implicitly_wait(25)
        self.dr.find_element_by_class_name("clearfix")
        time.sleep(1)
        need_myvxlan="True"
        need_k8s="True"
        elements=self.dr.find_elements_by_xpath("//main[@class='clearfix']/section[3]/div/table/tr")
        num=len(elements)
        if num>1:
            for n in range(2,num+1):
                expr="//main[@class='clearfix']/section[3]/div/table/tr["+str(n)+"]/"
                text_name=self.dr.find_element_by_xpath(expr+"td[1]/input").get_attribute('value')
                text_url=self.dr.find_element_by_xpath(expr+"td[3]/input").get_attribute('value')
                text_branch=self.dr.find_element_by_xpath(expr+"td[5]/input").get_attribute('value')
                print >>self.f,"\t" + text_name + "\t" + text_url + "\t" + text_branch
                print "\t" + text_name + "\t" + text_url + "\t" + text_branch
                if text_name == "myvxlan":
                    need_myvxlan="False"
                if text_name == "k8s":
                    need_k8s="False"
        if (need_myvxlan == "True"):
            self.dr.find_element_by_xpath("//main[@class='clearfix']/section[3]/div/button").click()
            time.sleep(1)
            expr = "//main[@class='clearfix']/section[3]/div/table/tr[" + str(num+1) + "]/"
            self.dr.find_element_by_xpath(expr+"td[1]/input").send_keys("myvxlan")
            self.dr.find_element_by_xpath(expr+"td[3]/input").send_keys(
            "https://github.com/leodotcloud/rancher-catalog.git")
            self.dr.find_element_by_xpath(expr+"td[5]/input").send_keys(Keys.CONTROL + "a")
            self.dr.find_element_by_xpath(expr+"td[5]/input").send_keys("hnatest2")
            print >> self.f,"\t"+"myvxlan\t"+"https://github.com/leodotcloud/rancher-catalog.git\t"+"hnatest2"
            print "\t"+"myvxlan\t"+"https://github.com/leodotcloud/rancher-catalog.git\t"+"hnatest2"
        if (need_k8s=="True"):
            self.dr.find_element_by_xpath("//main[@class='clearfix']/section[3]/div/button").click()
            time.sleep(1)
            expr = "//main[@class='clearfix']/section[3]/div/table/tr[" + str(num + 2) + "]/"
            self.dr.find_element_by_xpath(expr + "td[1]/input").send_keys("k8s")
            self.dr.find_element_by_xpath(expr + "td[3]/input").send_keys(
                "https://github.com/niusmallnan/rancher-catalog.git")
            self.dr.find_element_by_xpath(expr + "td[5]/input").send_keys(Keys.CONTROL + "a")
            self.dr.find_element_by_xpath(expr + "td[5]/input").send_keys("k8s-cn")
            print >>self.f,"\t"+"k8s\t"+"https://github.com/niusmallnan/rancher-catalog.git\t"+"k8s-cn"
        if (need_myvxlan == "True") or (need_k8s=="True"):
            self.dr.find_element_by_xpath(
                "//main[@class='clearfix']/section[3]/div/div[@class='ember-view footer-actions']/button").click()
            time.sleep(5)

    def container_ping_random(self):
        num = random.randint(0, len(self.agents_outer_ip) - 2)
        num2 = random.randint(0, len(self.agents_outer_ip) - 2)
        while (num2 == num):
            num2 = random.randint(0, len(self.agents_outer_ip) - 2)
        from TelnetTest import RTelnet
        dst_telnet = RTelnet(self.agents_outer_ip[num2],self.f)
        dst_telnet.login()
        dst_telnet.change_root()
        dst_all_container_id = dst_telnet.get_all_container_id()
        temp = random.randint(0, len(dst_all_container_id) - 1)
        m=0
        while True:
            try:
                re.search(r'(rancher)', dst_all_container_id.keys()[temp]).group(1)
                temp = random.randint(0, len(dst_all_container_id) - 1)
            except:
                try:
                    re.search(r'(ID)', dst_all_container_id.keys()[temp]).group(1)
                    temp = random.randint(0, len(dst_all_container_id) - 1)
                except:
                    try:
                        re.search(r'(hna)', dst_all_container_id.keys()[temp]).group(1)
                        temp = random.randint(0, len(dst_all_container_id) - 1)
                    except:
                        break
            m=m+1
            if m==100:
                break
        dst_container_id=dst_all_container_id.values()[temp]
        dst_container_ip = dst_telnet.get_container_ip(dst_container_id)
        dst_telnet.close()

        telnetH = RTelnet(self.agents_outer_ip[num],self.f)
        telnetH.login()
        telnetH.change_root()
        all_container_id = telnetH.get_all_container_id()
        n = random.randint(0, len(all_container_id) - 1)
        m = 0
        while True:
            if re.search(r'(rancher)', all_container_id.keys()[n]):
                n = random.randint(0, len(all_container_id) - 1)
                continue
            if re.search(r'(ID)', all_container_id.keys()[n]):
                n = random.randint(0, len(all_container_id) - 1)
                continue
            if re.search(r'(hna)', all_container_id.keys()[n]):
                n = random.randint(0, len(all_container_id) - 1)
                continue
            break
        container_id=all_container_id.values()[n]
        container_ip=telnetH.get_container_ip(container_id)
        print >> self.f, '\tFrom host:'+self.agents_inner_ip[num]+":"+ all_container_id.keys()[n]+"/"+container_ip+ "\tping\t" + "host:"+self.agents_inner_ip[num2]+":"+dst_all_container_id.keys()[temp] + "/" + dst_container_ip
        print >> self.f, '\t'+telnetH.container_ping(container_id, dst_container_ip)
        telnetH.close()

    def container_ping(self,container_id1,container_id2):
        pass

    def glb_check(self,glb_env_id,glb_stack_id,user_env_id='test'):
        all_stack_id=self.get_stack_all_id(glb_env_id)
        url = self.rancherserver_ip + "/env/" + str(glb_env_id) + "/apps/stacks/"+str(glb_stack_id)+"?which=all"
        self.dr.get(url)
        self.dr.implicitly_wait(15)
        self.dr.find_element_by_class_name("clearfix")
        time.sleep(2)
        actionItem = self.dr.find_element_by_xpath("//table[@class='grid fixed sized']/tbody/tr/td[@class='force-wrap service-detail']/span/a")
        url=actionItem.get_attribute("href")
        agent_inner_ip= re.search(r'(\d*\.\d*\.\d*\.\d*)',url).group(1)
#        print agent_inner_ip
        agent_outer_ip=self.agents_outer_ip[self.agents_inner_ip.index(agent_inner_ip)]
#        print agent_outer_ip
        from TelnetTest import RTelnet
        server_ip=re.search(r'(\d*\.\d*\.\d*\.\d*)',self.rancherserver_ip).group(1)
        dst_telnet = RTelnet(server_ip,self.f)
        dst_telnet.login()
        dst_telnet.change_root()
        glb_url="curl -i "+url+" -H 'host:abc.com'"
        rep=dst_telnet.send_cmd(str(glb_url)+'\n')
        dst_telnet.close()
        if re.search(r'(200\s*OK)',rep):
            print >> self.f,rep,"\n\tfrom "+server_ip+" curl test is successful! url:"+glb_url
            print rep
            print "\tfrom "+server_ip+" curl test is successful! url:"+glb_url
        if user_env_id=='test':
            self.glb_haproxy_config_check(glb_env_id,agent_outer_ip)
        else:
            self.glb_haproxy_config_check(user_env_id,agent_outer_ip)

    def glb_haproxy_config_check(self,env_id,host_ip):
        print >> self.f,"----GLB haproxy config check on host:"+host_ip
        print "----GLB haproxy config check on host:"+host_ip
        from TelnetTest import RTelnet
        dst_telnet = RTelnet(host_ip,self.f)
        dst_telnet.login()
        dst_telnet.change_root()
        all_container_id = dst_telnet.get_all_container_id()
        for key in all_container_id.keys():
            try:
                re.search(r'(lb)',key).group(1)
                container_id=all_container_id[key]
                break
            except:
                pass
        config_data =dst_telnet.get_haproxy_config(container_id)
        data=config_data.split('\n')
        data.pop()
        num=len(self.get_host_state(env_id))
        for i in range(1,num+1):
            print data[0-i]
            print >> self.f,"\t"+data[0-i]
        dst_telnet.close()

if __name__ == "__main__":
    rancher_server_ip = ['112.74.197.212', '10.45.166.186']
    agents_outer_ip = ["112.74.25.81", "120.25.65.45", "120.25.159.42", "120.76.145.193"]
    agents_inner_ip = ["10.170.47.124", "10.24.146.184", "10.116.141.136", "10.170.18.147"]

    rancher_version = "rancher/server:v1.6.0-rc3"
    engine = "Cattle"
    networking = "VXLAN"
    service_name = ["LBservice" + engine + networking, "Mysql" + engine + networking]

    NewTest = RancherServer('http://' + rancher_server_ip[0] + ":8080", agents_outer_ip, agents_inner_ip)
    NewTest.login()
    all_env = NewTest.get_all_env()

    print "---Deactivate host"
    for id in all_env.values():
        NewTest.delete_all_host(id)








