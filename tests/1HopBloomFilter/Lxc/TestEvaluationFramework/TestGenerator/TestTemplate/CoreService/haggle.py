#
# Copyright (c) 2012 SRI International and Suns-tech Incorporated
# Developed under DARPA contract N66001-11-C-4022.
# Authors:
#  Sam Wood (SW) 

#
# CORE uses this file to specify a "service" which generates bash
# scripts that are executed on each lxc at the beginning of test
# execution. 
#
''' 
'''

import os
import tempfile
from utils import *

from core.service import CoreService, addservice
from core.misc.ipaddr import IPv4Prefix, IPv6Prefix

USER=get_username()
TESTDIR=get_test_dir()
TESTAPP=get_app_name()
OUTPUTFILE=get_tmp_name()
CFGFILE=get_cfg_name()
FAILLOG=get_faillog_name()

class HaggleService(CoreService):
    ''' This is a sample user-defined service. 
    '''
    # a unique name is required, without spaces
    _name = "HaggleService"
    # you can create your own group here
    _group = "Utility"
    # list of other services this service depends on
    _depends = ()
    # per-node directories
    _dirs = ("/home/%s/.Haggle/" % (USER,) ,)
    # generated files (without a full path this file goes in the node's dir,
    #  e.g. /tmp/pycore.12345/n1.conf/)
    _configs = ('haggleservice.sh', )
    # this controls the starting order vs other enabled services
    _startindex = 50
    # list of startup commands, also may be generated during startup
    _startup = ('sh haggleservice.sh', )
    # list of shutdown commands
    _shutdown = ()

    @classmethod
    def generateconfig(cls, node, filename, services):
        ''' Return a string that will be written to filename, or sent to the
            GUI for user customization.
        '''
        cfg = "#!/bin/sh\n"
        cfg += "# this file, haggleservice.sh, auto-generated by HaggleService (haggle.py)\n"
        for ifc in node.netifs():
            cfg += 'echo "Node %s has interface %s"\n' % (node.name, ifc.name)
            # here we do something interesting 
            cfg += "\n".join(map(cls.subnetentry, ifc.addrlist))
            break
        cfg += "for e in $(/sbin/ifconfig | grep 'eth' | awk '{print $1;}'); do \n"
        cfg += "    subnet=$(/sbin/ifconfig $e | grep 'inet addr:' | cut -d: -f2 | awk -F. '{ print $3; }') \n"
        cfg += "    /sbin/ifconfig $e broadcast 10.0.${subnet}.255 netmask 255.255.255.0 \n"
        cfg += "done \n"
        cfg += "/sbin/route add default eth0\n"
        #cfg += "/sbin/ifconfig eth0 broadcast 10.0.0.255\n"
        cfg += "cp %s ~/.Haggle/config.xml\n" % (CFGFILE,) 
        # try to copy node specific file if available
        cfg += "cp %s ~/.Haggle/config.xml &> /dev/null\n" % (CFGFILE + ".%s" % node.name,)
        # the following lines are needed on some systems where /bin/su does not
        # bring over the LD_LIBRARY_PATH:
        # cfg += "/bin/su %s -l -c \"export LD_LIBRARY_PATH='/usr/local/lib/' && bash %s/start_haggle.sh %s\"\n" % (USER, TESTDIR, node.name)
        # cfg += "/bin/su %s -l -c \"export LD_LIBRARY_PATH='/usr/local/lib/' && sleep %%warmup%% && bash %s %s %s %s &\"\n" % (USER, TESTAPP, node.name, OUTPUTFILE + "." + node.
        # cfg += "/bin/su %s -l -c \"export LD_LIBRARY_PATH='/usr/local/lib/' && sleep %%warmup%% && bash %s/start_resource_monitor.sh &\"\n" % (USER, TESTDIR)
        # cfg += "/bin/su %s -l -c \"export LD_LIBRARY_PATH='/usr/local/lib/' && sleep %%warmup%% && bash %s/start_neighbor_monitor.sh %s &\"\n" % ("root", TESTDIR, USER)
        # cfg += "/bin/su %s -l -c \"export LD_LIBRARY_PATH='/usr/local/lib/' && bash %s/stop_haggle.sh %s %s\"\n" % (USER, TESTDIR, node.name, OUTPUTFILE + "." + node.name)
        cfg += "/bin/su %s -c \"bash %s/start_haggle.sh %s\" - \n" % (USER, TESTDIR, node.name)
        cfg += "/bin/su %s -c \"sleep %%warmup%% && bash %s %s %s %s &\" - \n" % (USER, TESTAPP, node.name, OUTPUTFILE + "." + node.name, FAILLOG)
        cfg += "/bin/su %s -c \"sleep %%warmup%% && bash %s/start_resource_monitor.sh &\" - \n" % (USER, TESTDIR)
        cfg += "/bin/su %s -c \"sleep %%warmup%% && bash %s/start_neighbor_monitor.sh %s &\" - \n" % ("root", TESTDIR, USER)
        cfg += "/bin/su %s -c \"bash %s/stop_haggle.sh %s %s\" - \n" % (USER, TESTDIR, node.name, OUTPUTFILE + "." + node.name)
        return cfg

    @staticmethod
    def subnetentry(x):
        ''' Generate a subnet declaration block given an IPv4 prefix string
            for inclusion in the config file.
        '''
        if x.find(":") >= 0:
            # this is an IPv6 address
            return ""
        else:
            net = IPv4Prefix(x)
            return 'echo "  network %s"' % (net)

# this line is required to add the above class to the list of available services
addservice(HaggleService)

