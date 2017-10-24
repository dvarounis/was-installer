#
# 
#

#Imports
import javax.xml.parsers.DocumentBuilderFactory as DocumentBuilderFactory
import javax.xml.parsers.DocumentBuilder as DocumentBuilder
import os
import sys
import AdminApp
import AdminConfig
import AdminTask
import AdminControl
import AdminNodeManagement
	
##########################################################################################
#WAS Application class
class WASapp:
	
	
	
	def __init__(self, earfile, hotfolder, wasenv):
		self.currentEnv = wasenv
		self.earfile = earfile
		self.sharedLibs = []
		self.webservers = []
		self.virtualhost = 'default_host'
		self.appName = ''
		self.targettype = ''
		self.targetname = ''
		self.nodename = ''
		#Is this a new app for the cell?
		self.isnewApp = 0
		#Fill the info above with the XML information
		self.getAppInfo()
		self.FullAppPath = hotfolder+'/'+earfile
		self.targetString = ''
		
		
	def printAppInfo(self):
		print "INFO - AppName:"+self.appName+" Target String:"+self.targetString	

	def isInstalled(self):
		instapps = AdminApp.list()
		instapplst = instapps.split('\r\n')
		for app in instapplst:
			if app == self.appName:return 1
		return 0
	
	def isIndexed(self):
		if len(self.appName) == 0:
			return 0
		else:
			return 1
	
	def getAppInfo(self):
		dbf = DocumentBuilderFactory.newInstance()
		db = dbf.newDocumentBuilder()
		dom = db.parse(self.currentEnv.topologyfile)
		apps = dom.getElementsByTagName('application')
		for i in range(apps.length):
		    currentAppElement = apps.item(i)
		    if self.earfile.startswith(currentAppElement.getAttribute('earfileptrn')):
		        self.targettype = currentAppElement.parentNode.getTagName()
		        self.targetname = currentAppElement.parentNode.getAttribute('name')
		        self.appName = currentAppElement.getAttribute('name')
		        
		        if self.targettype == 'server':
		        	self.nodename = currentAppElement.parentNode.getAttribute('nodename')
		        	
		        self.virtualhost = currentAppElement.getAttribute('vhost')
		        
		        sharedlibs = currentAppElement.getElementsByTagName('sharedlib')
		        for j in range(sharedlibs.length):
		       		self.sharedLibs.append(sharedlibs.item(j).getAttribute('name'))
		       	
		       	webservers = currentAppElement.getElementsByTagName('webserver')
		       	for w in range(webservers.length):
		       		self.webservers.append((webservers.item(w).getAttribute('name'),webservers.item(w).getAttribute('nodename')))
		       	
	
	def FindTargetString(self):
		if self.targettype == 'server':
			self.targetString = 'WebSphere:cell='+self.currentEnv.CellName+',node='+self.nodename+',server='+self.targetname
		elif self.targettype == 'cluster':
			self.targetString = 'WebSphere:cell='+self.currentEnv.CellName+',cluster='+self.targetname
			
		
	def installApp(self):
		if not self.isInstalled():
			self.isnewApp = 1
			self.installNewApp()
		else:
			self.updateApp()
	
	def updateApp(self):
		
		self.setTargetWebServers()
		
		paramsString = '[ -operation update -contents \''+self.FullAppPath+'\' -nopreCompileJSPs -installed.ear.destination $(APP_INSTALL_ROOT)/'+self.currentEnv.CellName+' -distributeApp -nouseMetaDataFromBinary -nodeployejb -createMBeansForResources -reloadEnabled -reloadInterval 0 -nodeployws -validateinstall warn -noprocessEmbeddedConfig -filepermission .*\.dll=755#.*\.so=755#.*\.a=755#.*\.sl=755 -noallowDispatchRemoteInclude -noallowServiceRemoteInclude -asyncRequestDispatchType DISABLED -nouseAutoLink -noenableClientModule -clientMode isolated -novalidateSchema -MapModulesToServers [[ .* .* '+self.targetString+' ]] -MapWebModToVH [[.* .* '+self.virtualhost+' ]]]'
		
		paramsString = self.setSharedLibs(paramsString)
		
		print 'Params String: '+paramsString
		
		AdminApp.update(self.appName, 'app', paramsString )

	def installNewApp(self):
		
		self.setTargetWebServers()
		
		paramsString = '[ -nopreCompileJSPs -distributeApp -nouseMetaDataFromBinary -nodeployejb -appname \''+self.appName+'\' -createMBeansForResources -reloadEnabled -reloadInterval 0 -nodeployws -validateinstall warn -noprocessEmbeddedConfig -filepermission .*\.dll=755#.*\.so=755#.*\.a=755#.*\.sl=755 -noallowDispatchRemoteInclude -noallowServiceRemoteInclude -asyncRequestDispatchType DISABLED -nouseAutoLink -noenableClientModule -clientMode isolated -novalidateSchema -MapModulesToServers [[ .* .* '+self.targetString+' ]] -MapWebModToVH [[.* .* '+self.virtualhost+' ]]]'
		
		paramsString = self.setSharedLibs(paramsString)
		
		print 'Params String: '+paramsString
		
		AdminApp.install(self.FullAppPath, paramsString )
		
	
	def setTargetWebServers(self):
		webtargets=''
		if len(self.webservers) > 0:
			for w,n in self.webservers:
				webtargets+='+WebSphere:cell='+self.currentEnv.CellName+',node='+n+',server='+w
		self.targetString += webtargets

	def setSharedLibs(self, paramsString):
		
		if len(self.sharedLibs) > 0:
			paramsString = paramsString[:-1]+' -MapSharedLibForMod [[ \''+self.appName+'\' META-INF/application.xml "'
			shlibStr = self.sharedLibs.pop()
			#Multiple Shared Libs are declared as <shlib1>+<shlib2>+...
			while len(self.sharedLibs) > 0:
				shlibStr = shlibStr+'+'+self.sharedLibs.pop()
			
			paramsString = paramsString+shlibStr+'" ]]'
		
		return paramsString


##########################################################################################
#WAS Environment class
class WASenv:
	
	def __init__(self,topologyfile):
		self.CellName = AdminControl.getCell()
		self.timeout = 1200
		self.topologyfile = 'file:'+topologyfile

	def SaveConfig(self):
		AdminConfig.save()	

	def SyncNodes(self):
		AdminNodeManagement.syncActiveNodes()

	def rolloutUpdateApp(self, appName):
		updateAppCommand = '[ -ApplicationNames \'' + appName + '\' -timeout ' + str(self.timeout) + ' ]'
		AdminTask.updateAppOnCluster(updateAppCommand)

##########################################################################################

def listEARs(hotfolder):
	earlist=[]
	print 'Listing EARs to deploy from '+hotfolder+':'
	
	if os.path.isdir(hotfolder):
		fileslist = os.listdir(hotfolder)
		
		for f in fileslist:
			if f.endswith('.ear'):
				earlist.append(f)
		print earlist
		return earlist
	else:
		print earlist
		return earlist

def printDeploymentPlan(deplan):
	for tstr in deplan.keys():
		print 'Target: '+ tstr
		for app in deplan[tstr]:
			print '	App: '+str(app.appName)+' SharedLibs: '+str(app.sharedLibs)+' Web Servers: '+str(app.webservers)+' VirtualHost: '+str(app.virtualhost)

def createDeploymentPlan(earlist, wasenv):
	appsQueue = []
	for earfile in earlist:
		app = WASapp(earfile, hotfolder, wasenv)
		appsQueue.append(app)
	
	Deploymenttargets = {}
	targetQueue = []
	
	for app in appsQueue:
		if app.isIndexed():
			app.FindTargetString()
			if not app.targetString in Deploymenttargets.keys():
				Deploymenttargets[app.targetString] = [ app ]
			else:
				Deploymenttargets[app.targetString].append(app)
		else:
			print 'We could not find information for: '+app.earfile
	
	return Deploymenttargets

def installApps(deplan, wasenv, SSync):
	 for tstr in deplan.keys():
	 	if tstr.find('cluster') < 0 or SSync == 1:
	 		#installation in server or Save/Synchronize Mode
	 		apps = deplan[tstr]
	 		for app in apps:
	 			app.installApp()
			wasenv.SaveConfig()
			wasenv.SyncNodes()
		else:
			#installation in Cluster  
			apps = deplan[tstr]
			lastUpdatedAppName = ''
			print "Cluster Name: "+tstr
	 		for app in apps:
	 			app.installApp()
	 			if not app.isnewApp: lastUpdatedAppName = app.appName
			wasenv.SaveConfig()
			
			if len(lastUpdatedAppName) > 0:
				print "Making the Rollout Update!"
				wasenv.rolloutUpdateApp(lastUpdatedAppName)
			else:
				#This is the case where all apps are new ones, i.e. no update, just sync
				wasenv.SyncNodes()
				
def deployApps(hotfolder,topologyfile, SSync=0):
	earlist = listEARs(hotfolder)
	currentWASEnv = WASenv(topologyfile)
	if len(earlist) > 0:
		Depltargets = createDeploymentPlan(earlist,currentWASEnv)
		printDeploymentPlan(Depltargets)
		installApps(Depltargets, currentWASEnv, SSync)
			
##########################################################################################
if __name__ == '__main__':
	hotfolder = ''
	topologyfile = ''	
	if len(sys.argv) == 2:
		hotfolder = sys.argv[0]
		topologyfile = sys.argv[1]
		deployApps(hotfolder,topologyfile)
		
	elif len(sys.argv) == 3 and sys.argv[0] == '-S':
		SSync = 1 
		hotfolder = sys.argv[1]
		topologyfile = sys.argv[2]
		deployApps(hotfolder,topologyfile,SSync)
	else:
		message = '''
		Usage: myscript.py [-S] <EAR hotfolder path> <topology xml file path> 
		Options
		-S (optional) 
			Make no Cluster Rollout, instead  just Save and Syncronize whatever the topology
		'''
		print message
			
	
