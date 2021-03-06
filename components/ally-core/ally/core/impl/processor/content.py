'''
Created on Aug 30, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides a processor that provides the request content as an invoking argument.
'''

from ally.api.model import Content
from ally.api.type import Input
from ally.container.ioc import injected
from ally.core.spec.codes import Code, BAD_CONTENT
from ally.core.spec.resources import Invoker
from ally.design.context import Context, requires, optional, asData, defines
from ally.design.processor import HandlerProcessorProceed
from ally.support.util_io import IInputStream
from collections import Callable
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    invoker = requires(Invoker)
    arguments = requires(dict)

class RequestContentData(Context):
    '''
    The request content context used for the content.
    '''
    # ---------------------------------------------------------------- Optional
    name = optional(str)
    type = optional(str)
    charSet = optional(str)
    length = optional(int)

class RequestContent(RequestContentData):
    '''
    The request content context.
    '''
    # ---------------------------------------------------------------- Required
    source = requires(IInputStream)
    # ---------------------------------------------------------------- Optional
    fetchNextContent = optional(Callable)

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defines
    code = defines(Code)
    text = defines(str)

# --------------------------------------------------------------------

@injected
class ContentHandler(HandlerProcessorProceed):
    '''
    Handler that provides the content as an argument if required.
    '''

    def __init__(self):
        '''
        Construct the content handler.
        '''
        super().__init__()

    def process(self, request:Request, response:Response, requestCnt:RequestContent=None, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response

        if Response.code in response and not response.code.isSuccess: return # Skip in case the response is in error
        assert isinstance(request.invoker, Invoker), 'Invalid request invoker %s' % request.invoker

        for inp in request.invoker.inputs:
            assert isinstance(inp, Input)

            if inp.type.isOf(Content):
                if requestCnt is None:
                    response.code, response.text = BAD_CONTENT, 'Required a request content follow up'
                    return
                assert isinstance(requestCnt, RequestContent), 'Invalid request content %s' % requestCnt
                assert isinstance(requestCnt.source, IInputStream), 'Invalid request content source %s' % requestCnt.source

                request.arguments[inp.name] = ContentData(requestCnt)
                assert log.debug('Successfully provided the next content for input (%s)', inp.name) or True

# --------------------------------------------------------------------

class ContentData(Content):
    '''
    A content model based on the request.
    '''
    __slots__ = ('_content', '_closed')

    def __init__(self, content):
        '''
        Construct the content.
        
        @param request: RequestContent
            The request content.
        '''
        assert isinstance(content, RequestContent), 'Invalid request content %s' % content
        assert isinstance(content.source, IInputStream), 'Invalid content source %s' % content.source
        super().__init__(**asData(content, RequestContentData))

        self._content = content
        self._cloased = False

    def read(self, nbytes=None):
        '''
        @see: Content.read
        '''
        if self._cloased: raise ValueError('I/O operation on a closed content file')
        return self._content.source.read(nbytes)

    def next(self):
        '''
        @see: Content.next
        '''
        if self._cloased: raise ValueError('I/O operation on a closed content file')

        self._cloased = True
        if RequestContent.fetchNextContent in self._content: content = self._content.fetchNextContent()
        else: content = None

        if content is not None: return ContentData(content)
