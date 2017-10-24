# was-installer
## WAS Application Deployment Script

WAS-installer is a tool for deploying a group of applications (delivered in EAR form) in a WAS Cell. 
It works using a system directory (preferably on dmgr server) as a hotfolder where deployable EARs lie and an xml document (conventionally named topology.xml) that describes the Application Topology in the Cell.
The tool is composed by two files:  
1. A jython file named installer.py containing the wsadmin code that does the actual job 
2. A wrapper bash script named installer.sh that collects all EAR files (e.g. from a Nexus Repository), manages the logs etc. and then calls installer.py as a wsadmin script.


## Quick Description of Operation  
The tool lists all EAR files in given hotfolder and based on their filename (which is declared in topology.xml) decides where they should be deployed, whether this is a server or a cluster. If more than one EARs are in the hotfolder, it groups them by target, i.e. by server or cluster and then starts installing them to each target, one target after the other. In the case of the cluster the tool will perform a Rollout update unless we provide a parameter to force a Save/Synchronize operation. 
In addition, it doesn’t matter whether the apps are new or already deployed in Cell, the tool will install them in the same way based on the parameters given in topology.xml. 
However, in the case of a new Application the tool will not start the newly deployed app, this has to be done manually. 

## Supported Installation Parameters 
The following installation parameters are supported when defining an application: 
- Virtual Host of the App (should be the same for all web modules of the app) 
- Shared libraries connected to the App 
- Web Servers Mapped Those parameters are provided by user in topology.xml. 

## Supported Environments
The tool is tested to work in Linux OS and in WebSphere Application Server 8.5 ND Traditional Environments. 
Also it is tested in WebSphere Portal 8.5 Clusters. With minor modifications the installer.py (i.e. different Line Endings) will work on Windows OS while installer.sh is tested to work in Cygwin environment.
