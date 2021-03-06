'''
Created on Aug 9, 2011

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the method override header handling.
'''

from ally.api.config import DELETE, GET, INSERT, UPDATE
from ally.container.ioc import injected
from ally.core.http.spec.codes import INVALID_HEADER_VALUE
from ally.core.http.spec.server import IDecoderHeader
from ally.core.spec.codes import Code
from ally.design.context import Context, requires, defines
from ally.design.processor import HandlerProcessorProceed
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    decoderHeader = requires(IDecoderHeader)
    method = requires(int)

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    code = defines(Code)
    text = defines(str)
    errorMessage = defines(str)

# --------------------------------------------------------------------

@injected
class MethodOverrideDecodeHandler(HandlerProcessorProceed):
    '''
    Provides the method override processor.
    '''

    nameXMethodOverride = 'X-HTTP-Method-Override'
    # The header name for the method override.
    methods = {
              'DELETE' : DELETE,
              'GET' : GET,
              'POST' : INSERT,
              'PUT' : UPDATE,
              }
    methodsOverride = {
                       GET:{GET, DELETE},
                       INSERT:{INSERT, UPDATE},
                       }
    # A dictionary containing as a key the original method and as a value the methods that are allowed for override.

    def __init__(self):
        assert isinstance(self.nameXMethodOverride, str), 'Invalid method override name %s' % self.nameXMethodOverride
        assert isinstance(self.methods, dict), 'Invalid methods %s' % self.methods
        assert isinstance(self.methodsOverride, dict), 'Invalid methods override %s' % self.methodsOverride
        super().__init__()

    def process(self, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Overrides the request method based on a provided header.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        if Response.code in response and not response.code.isSuccess: return # Skip in case the response is in error

        assert isinstance(request.decoderHeader, IDecoderHeader), 'Invalid header decoder %s' % request.decoderHeader

        value = request.decoderHeader.retrieve(self.nameXMethodOverride)
        if value:
            over = self.methods.get(value.upper())
            if not over:
                response.code, response.text = INVALID_HEADER_VALUE, 'Invalid method %s' % value
                response.errorMessage = 'Invalid override method \'%s\' for header \'%s\'' % \
                (value, self.nameXMethodOverride)
                return

            allowed = self.methodsOverride.get(request.method)
            if not allowed:
                response.code, response.text = INVALID_HEADER_VALUE, 'Cannot override method'
                return

            if over not in allowed:
                response.code, response.text = INVALID_HEADER_VALUE, 'Override method \'%s\' not allowed' % value
                return

            assert log.debug('Successfully overridden method %s with %s', request.method, over) or True
            request.method = over
