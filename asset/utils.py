from asset.models import *

import os,time,commands
from salt.client import LocalClient

class goPublish:
    def __init__(self,env):
        self.env = env
        self.saltCmd = LocalClient()


    def getNowTime(self):
        return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(time.time()))



    def deployGo(self,name,services):

        self.name = name
        self.services = services
        hostInfo = {}
        result = []

        minionHost = commands.getstatusoutput('salt-key -l accepted')[1].split()[2:]
        groupname = gogroup.objects.all()
        for name in groupname:
            if self.name == name.name:
                for obj in goservices.objects.filter(env=self.env).filter(group_id=name.id):
                    for saltname in minion.objects.filter(id=obj.saltminion_id):
                        saltHost = saltname.saltname
                        if saltHost not in minionHost:
                            notMinion = 'No minions matched the %s host.' % saltHost
                            result.append(notMinion)
                        if self.services == 'all':
                            golist = [obj.name]
                            if hostInfo.has_key(saltHost):
                                services.append(obj.name)
                            else:
                                services = golist
                                hostInfo[saltHost] = services
                        else:
                            if obj.name == self.services:
                                golist = [self.services]
                                hostInfo[saltHost] = golist




        for host,goname in hostInfo.items():
                    deploy_pillar = "pillar=\"{'project':'" + self.name + "'}\""

                    os.system("salt '%s' state.sls logs.gologs %s" % (host, deploy_pillar))
                    currentTime = self.getNowTime()
                    self.saltCmd.cmd('%s' % host, 'cmd.run', ['mv /srv/%s/%s /tmp/%s/%s_%s' % (self.name, self.name, self.name, self.name, currentTime)])
                    svn = self.saltCmd.cmd('%s' % host, 'cmd.run', ['svn update --username=deploy --password=ezbuyisthebest --non-interactive /srv/%s' % self.name])
                    result.append(svn)
                    allServices = " ".join(goname)
                    restart = self.saltCmd.cmd('%s'%host,'cmd.run',['supervisorctl restart %s'%allServices])
                    result.append(restart)




        return result

    def go_revert(self,project,revertFile,host):

        self.project = project
        self.revertFile = revertFile
        self.host = host
        result = []

        projectPwd = "/srv/" + self.project + "/" + self.project
        currentTime = self.getNowTime()

        rename = "/tmp/revert/" + self.project + '_revert_' + currentTime
        runCmd = "'mv " + projectPwd + " " + rename + "'"

        os.system("salt %s state.sls logs.revert" % self.host)

        self.saltCmd.cmd('%s' % self.host,'cmd.run',['%s' % runCmd])

        revertResult = commands.getstatusoutput("salt '%s' cmd.run 'cp /tmp/%s/%s /srv/%s/%s'" %(self.host,self.project,self.revertFile,self.project,self.project))
        if revertResult[0] == 0:
            for obj in goservices.objects.filter(env=self.env):
                if obj.group.name == self.project and self.host == obj.saltminion.saltname:
                    #os.system("salt %s cmd.run 'supervisorctl restart %s'"%(self.host,obj.name))
                    restart = self.saltCmd.cmd('%s' % self.host,'cmd.run',['supervisorctl restart %s' % obj.name])
                    result.append(restart)


            mes = 'revert to %s version is successful.' % revertFile
            mes = {self.host:mes}
            result.append(mes)
        else:
            mes = 'revert to %s version is failed.' % revertFile
            mes = {self.host: mes}
            result.append(mes)
        return result


    def goConf(self):
        hostname = []
        result = []
        if self.env == '1' or self.env == '2':
            for obj in goservices.objects.filter(env=self.env):
                hostname.append(str(obj.saltminion.saltname))
        hostname = list(set(hostname))
        confCmd = "svn update --username=deploy --password=ezbuyisthebest --non-interactive /srv/goconf"
        for h in hostname:
            confResult = self.saltCmd.cmd('%s'%h,'cmd.run',['%s'%confCmd])
            result.append(confResult)

        return result


class goServicesni:
    def __init__(self,projectName):
        self.projectName = projectName

    def getServiceName(self):
        services = []
        groupname = gogroup.objects.all()
        for group in groupname:
            if self.projectName == group.name:
                for obj in goservices.objects.filter(group=group.id):
                    services.append(obj)

        return services




