"""
Server-Sent Events (SSE) Renderer for Django REST Framework

This renderer enables DRF views to return Server-Sent Events streams,
bypassing the default Content Negotiation mechanism.

Author: AI Platform Team
Date: 2025-11-24
"""

from rest_framework.renderers import BaseRenderer


class ServerSentEventRenderer(BaseRenderer):
    """
    Custom renderer for Server-Sent Events (SSE) streams.
    
    This renderer allows DRF views to return StreamingHttpResponse
    with content_type='text/event-stream' without triggering
    406 Not Acceptable errors during content negotiation.
    
    Usage:
        @action(detail=False, methods=['get'], renderer_classes=[ServerSentEventRenderer])
        def stream_progress(self, request):
            def event_stream():
                yield f'data: {{"message": "hello"}}\n\n'
            
            return StreamingHttpResponse(
                event_stream(),
                content_type='text/event-stream'
            )
    """
    
    media_type = 'text/event-stream'
    format = 'sse'
    charset = 'utf-8'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render method for SSE.
        
        Note: For StreamingHttpResponse, this method is typically not called
        as the response is already in the correct format. This is here to
        satisfy DRF's content negotiation process.
        """
        return data

