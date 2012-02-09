'''
Created on Jan 12, 2012

@package Newscoop
@copyright 2011 Sourcefabric o.p.s.
@license http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup registry for the plugins.
'''

from ally.container import ioc
from ally.container.proxy import proxyWrapForImpl
from ally.core.spec.resources import ResourcesManager
from cdm.impl.local_filesystem import LocalFileSystemLinkCDM, HTTPDelivery
from cdm.spec import ICDM
from functools import partial

# --------------------------------------------------------------------

def registerService(service, binders = None):
    '''
    A listener to register the service.
    
    @param service: object
        The service to be registered.
    @param binders: list[Callable]|tuple(Callable)
        The binders used for the registered services.
    '''
    proxy = proxyWrapForImpl(service)
    if binders:
        for binder in binders: binder(proxy)
    services().append(proxy)

def addService(*binders):
    '''
    Create listener to register the service with the provided binders.
    
    @param binders: arguments[Callable]
        The binders used for the registered services.
    '''
    return partial(registerService, binders = binders)

# --------------------------------------------------------------------

@ioc.config
def gui_server_uri():
    ''' The HTTP server URI, basically the URL where the javascript content should be fetched from'''
    return '/content/js/'

@ioc.config
def gui_repository_path():
    ''' The repository absolute or relative (to the distribution folder) path '''
    return 'workspace'

# --------------------------------------------------------------------

@ioc.entity
def cdmGUI() -> ICDM:
    '''
    The content delivery manager (CDM) for the plugin's static resources
    '''
    delivery = HTTPDelivery()
    delivery.serverURI = gui_server_uri()
    delivery.repositoryPath = gui_repository_path()
    cdm = LocalFileSystemLinkCDM()
    cdm.delivery = delivery
    return cdm

@ioc.entity
def resourcesManager() -> ResourcesManager:
    import ally_deploy_plugin
    return ally_deploy_plugin.resourcesManager

@ioc.entity
def services():
    '''
    The plugins services that will be registered automatically.
    '''
    return []

@ioc.start
def register():
    import ally_deploy_plugin
    ally_deploy_plugin.services = services()
