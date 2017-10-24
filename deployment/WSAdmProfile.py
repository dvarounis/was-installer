import os
from java.util import Date
from java.text import SimpleDateFormat
from java.lang import System

import sys


# Profile module to expose the wsadmin "Admin objects" and load libraries
# specified by the javaoption "wsadmin.jython.libraries".  (See comments below
# for more details about how to specify libraries to be loaded.)
# 
# NOTE: This profile is intended for use when the standard script libraries
# that come with WAS v7, v8, v8.5 are not used.  (You can rename the directory 
# where the libraries are located to avoid using them.)  They are located in:
#  <WAS_INSTALL_ROOT>/scriptLibraries
#
# This profile can also be used when a more recent version of Jython is used.  
# You can download a more recent Jython and extract the archive into a directory 
# in <WAS_INSTALL_ROOT>/optionalLibraries.  Move the existing jython directory to 
# something like jython-v2.1.  Extract the newer Jython into a directory such as 
# jython-v2.5.2.  Make a symlink with the name jython to the newer version:  
#      ln -s jython-v2.5.2 jython  
# To change back to using the Jython that comes with WAS, remove the jython symlink 
# and recreate it pointing to the older jython directory:
#      ln -s jython-v2.1 jython 
# 
# To load your custom Jython libraries, don't use wsadmin.script.libraries as this
# triggers the loading of your library by the wsadmin runtime.  Unfortunately the
# wsadmin runtime doesn't just build the sys.path it also imports any Jython modules
# it finds.  This is inappropriate for a couple of reasons.  First there is no reason
# to import all the library modules when only some of them may be used.  Second
# there may be dependencies among the library modules and the order in which the 
# modules gets loaded is independent of potential dependencies.  (The order in which
# library modules is loaded is essentially the lexical order of the pathnames of the
# library module files.)
#
# When you don't use the wsadmin initialization that comes with the standard 
# libraries you have to set up the sys.path with the locations of the modules
# in the library pointed to by wsadmin.jython.libraries.  The initialization
# of wsadmin changes such that sys.path doesn't include the directories
# pointed to be wsadmin.jython.libraries.  

# This approach to setting up sys.modules with the wsadmin objects comes
# from the Gibson, McGrath, Bergman book: WebSphere Application Server
# Administration using Jython.
WASObjects = { 'AdminApp': AdminApp,
               'AdminConfig': AdminConfig,
               'AdminControl': AdminControl,
               'Help': Help
             }

# Check to see if AdminTask is in the namespace 
# and if it is, add it to the WASObjects to be added
# to sys.modules.  AdminTask won't be in the namespace
# if wsadmin is not connected to a server, e.g., connType=None.
if 'AdminTask' in dir():
    WASObjects[ 'AdminTask' ] = AdminTask
#endIf

# Now copy WASObjects into the sys.modules dictionary.
sys.modules.update( WASObjects )

###############################################################################
# The rest of this profile is used to set up sys.path so a Jython library 
# can be used conveniently.  

# _getTimeStamp() is for a info trace to stdout.
def _getTimeStamp():
  # WAS style time stamp.  SimpleDateFormat is not thread safe.
  sdf = SimpleDateFormat("yy/MM/dd HH:mm:ss.sss z")
  return '[' + sdf.format(Date()) + ']'
#endDef

#  
# The _updateLibraryPath() method is called from the os.path.walk()
# method with the three arguments.  See Jython Essentials for a 
# description of the os.path.walk() method.  (Or search the Internet
# for doc on os.path.walk().)

# PVS: 9/12/2011 - NOTE: The sys.path needs to contain all directories
# in the path that have an __init__.py file in them in order to properly
# import modules qualified with a package name.  At one point I was thinking
# that if a directory only had an __init__.py file in it, it didn't need to
# be on the sys.path, however that is not the case.
#
# PVS: 9/12/2011 - NOTE: When using recent versions of Jython the strings 
# are created in unicode.  You will see unicode strings in sys.path.  In my
# testing the unicode strings in sys.path have not been a problem.  At one
# point I was coercing dirname in the method below to an ASCII string using
# str(dirname) to make all sys.path entries from this method look like the
# other entries that get loaded by the Jython runtime.  Since unicode strings
# work, I removed the str(dirname) invocation and just appeded dirname directly.
#
#
def _updateLibraryPath(libPath,dirname,files):
  for pathname in files:
    if (pathname.endswith('.py')):
      # At least one Jython module in the directory
      libPath.append(dirname)
      break
    #endIf
  #endFor
  return libPath
#enDef

# The _createJythonLibraryPath() method can be used to return a list
# of directories that have Jython (.py) modules defined in them that
# are somewhere in the directory tree rooted at the given library 
# directory root.  This method reproduces the wsadmin behavior of loading
# a library using the javaoption:
# -javaoption "-Dwsadmin.jython.libraries=<whatever>"
#
# NOTE: You can use java.lang.System.getProperty("wsadmin.jython.libraries")
# to get the -D property value, thus you can use the same command line
# option to set up a Jython library path as WAS v7 and later versions.
#
# NOTE: Append the result of this method to sys.path using extend()
#
def _createJythonLibraryPath(libRootDirectoryPath):
  libPath = []
  os.path.walk(libRootDirectoryPath,_updateLibraryPath,libPath)
  return libPath
#endDef


# The list of libraries associated with wsadmin.jython.libraries is assumed
# to be separated by semi-colon.  Each "library" is the path to the root 
# directory of the library directory tree.
jythonLibraries = System.getProperty("wsadmin.jython.libraries")
if (jythonLibraries):
  jythonLibraries = jythonLibraries.split(';')
  for jythonLibrary in jythonLibraries:
    timeStamp = _getTimeStamp()
    print "%s WASv70Profile INFO updating sys.path with library rooted at: %s" % (timeStamp,jythonLibrary)
    libraryPath = _createJythonLibraryPath(jythonLibrary)
    sys.path.extend(libraryPath)
  #endFor
else:
  timeStamp = _getTimeStamp()
  print "%s WASv70Profile INFO No wsadmin.jython.libraries defined." % timeStamp
#endIf

# Remove unnecessary names from the namespace
# The names that are directly in a del statement are sure to be defined.
del os, System, Date, SimpleDateFormat, WASObjects, 
del _updateLibraryPath, _getTimeStamp, _createJythonLibraryPath, timeStamp

# Delete names that are in the namespace only if there are wsadmin.jython.libraries.
# Jython throws an exception if you try to delete a name that isn't in the namespace.
if (jythonLibraries):
  del jythonLibrary, libraryPath
#endIf
# Now delete the last things to be used
del jythonLibraries
