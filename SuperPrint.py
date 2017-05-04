# -*- coding:utf-8 -*-

'''
Nothing Here......
'''

import telnetlib,time,threading,os

#定义异常类,从Exception基类继承,重写__str__
class telnetException(Exception):

    #异常类构造方法
    def __init__(self,host,errcode,errmsg,logintype):
        self.host=host
        self.errcode=errcode
        self.errmsg=errmsg
        self.logintype=logintype

    #返回的异常信息
    def __str__(self):
        return "<%s 到 %s 主机时发生错误,错误码 %s,错误信息:%s>" % (self.logintype,self.host,self.errcode,self.errmsg)

# 连接类,支持Telnet,SSH
class Klogintype(object):

    # 默认采用telnet连接,可以在实例化的时候直接给定该参数
    def __init__(self,logintype='telnet',kconobj=telnetlib.Telnet()):
        self.logintype=logintype
        self.kconobj=kconobj

    # telnet4000登陆调试方法
    def KtelnetCon(self,host,port,username,password):

        try:
            self.kconobj.open(host,port)
            self.kconobj.read_until("Username:")
            self.kconobj.write(username+"\r\n")
            self.kconobj.read_until("Password:")
            self.kconobj.write(password+"\r\n")

        except:
            print telnetException(host,300,"服务器未响应",self.logintype)

    #23端口登陆方法
    def KtelnetCon23(self,host,port,username,password):

        try:
            self.kconobj.open(host,port)
            #self.kconobj.read_until("nvr1825 login: ")
            self.kconobj.expect(['.*login: '],5)
            self.kconobj.write(username+"\r\n")
            self.kconobj.read_until("Password: ")
            self.kconobj.write(password+"\r\n")

        except:
            print telnetException(host,300,"服务器未响应",self.logintype)


    #发送前置字符方法
    def Ksendfstr(self,forwardstr):

        #发送命令前查找前置字符
        self.kconobj.expect([forwardstr],5)


    #命令交互
    def Ktelnetsbc(self,commandname,forwardstr):

        #发送命令参数
        self.kconobj.write(commandname+"\r\n")
        msg=self.kconobj.read_until(forwardstr)

        #解决中文乱码
        print msg.decode('gbk')


    #实时打印方法,可做采集用,默认采集到文本中
    def KtelnetRpp(self,commandname,logpath):

        self.kconobj.write(commandname+"\r\n")
        fileHandle=open(logpath,'w+')
        while self.kconobj.read_some():
            time.sleep(10)

            #非阻塞方式读取
            klog=self.kconobj.read_very_eager()

            print klog #debug

            #写入日志
            fileHandle.write(klog)

        fileHandle.close()

    #关闭通道方法
    def kcloseme(self):
        self.kconobj.close()


#定义一个采集类,从Thread类中继承
class Kcollection(threading.Thread):
    def __init__(self,commandname,logpath):
        #调用父类构造方法
        threading.Thread.__init__(self)
        self.commandname=commandname
        self.logpath=logpath

    def run(self):
        k=Klogintype()
        k.KtelnetRpp(self.commandname,self.logpath)

#定义一个菜单
def showmenu():

    print ('''


    *************** 常用信息快速查看 ***************

    1.查看XXX版本信息
 

    **************** 自动化/采集任务/打印自动捕获 *************

    14.执行vmstat性能参数采集(默认规则,关注bi,bo,si,so,cpu分布)
    15.查看网口相关信息,丢包情况等
    16.执行批量采集任务,多线程采集不同设备(vmstat)
    17.清理采集日志


    ''' )


if __name__=="__main__":

    #显示菜单
    showmenu()
    userinput=raw_input("请输入你要执行的操作选项:")

    #必要的实例化
    k=Klogintype()
    k.KtelnetCon('172.16.114.93',4000,'admin','admin123')

    k.Ksendfstr("nvr->")

    while not userinput:
        userinput=raw_input("请务必输入一个选项:")
    else:
        #提交主体命令区域,显示一些常用信息
        if userinput=='1':
            k.Ktelnetsbc('nvrver',"nvr->")
        elif userinput=='2':
            k.Ktelnetsbc('mpu',"nvr->")
        elif userinput=='3':
            k.Ktelnetsbc('pdec',"nvr->")
        elif userinput=='4':
            k.Ktelnetsbc('pdvs',"nvr->")
        elif userinput=='5':
            k.Ktelnetsbc('plylist',"nvr->")
        elif userinput=='6':
            k.Ktelnetsbc('hdinfo',"nvr->")
        elif userinput=='7':
            k.Ktelnetsbc('ptinfo',"nvr->")
        elif userinput=='8':
            k.Ktelnetsbc('reclist',"nvr->")
        elif userinput=='9':
            k.Ktelnetsbc('rsinfo',"nvr->")
        elif userinput=='10':
            k.Ktelnetsbc('sci',"nvr->")
        elif userinput=='11':
            k.Ktelnetsbc('shwenc',"nvr->")
        elif userinput=='12':
            k.Ktelnetsbc('ssw',"nvr->")
        elif userinput=='13':
            k.Ktelnetsbc('vtduver',"nvr->")
        elif userinput=='14':
            #采集任务需要重新初始化,Debug,一般用批量采集
            k.KtelnetCon23('172.16.114.93',23,'admin','kedacomIPC')
            k.Ksendfstr('admin@nvr.*:~$')
            t=Kcollection('vmstat 1',r'C:\KSuperPrint-Log.txt')
            t.start()
            print "成功启动一个采集线程: %s | 状态:正在运行中......" % t.name

        elif userinput=='16':
            #执行批量采集任务
            iplists=raw_input("请输入批量采集设备的IP地址,用英文逗号隔开:")

            for ip in iplists.split(','):

                k=Klogintype()
                k.KtelnetCon23(ip,23,'admin','kedacomIPC')
                k.Ksendfstr("admin@nvr.*:~$")
                t=Kcollection('vmstat 1',r'C:\KSuperPrint-Log-'+ip+".txt")
                t.start()
                print "成功启动一个采集线程: %s | 状态:正在运行中......" % t.name
        elif userinput=='17':
                pass