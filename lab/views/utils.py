from urllib.parse import quote

from django.core.cache import cache
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import TemplateView

from lab.models import Project
from lab.utils.diagram import ProjectDiagram
from lab.utils.gns3 import get_gns3_session, gns3_base_url


class SymbolView(View):
    @staticmethod
    def get(_request, symbol_id, *_args, **_kwargs):
        symbol = cache.get('symbol|' + symbol_id)
        if not symbol:
            session = get_gns3_session()

            # Check that it exists
            symbols = session.get(gns3_base_url + '/v2/symbols').json()
            for symbol in symbols:
                if symbol['symbol_id'] == symbol_id:
                    break
            else:
                return HttpResponseNotFound()

            # And retrieve
            symbol = session.get(gns3_base_url + '/v2/symbols/' + quote(symbol_id) + '/raw')
            cache.set('symbol|' + symbol_id, symbol, 3600)

        return HttpResponse(symbol, content_type=symbol.headers['content-type'])


class DrawingView(TemplateView):
    template_name = 'lab/drawing.html'

    def get_context_data(self, project_id, show_state=True, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, pk=project_id)
        context.update(ProjectDiagram(project).get_data(show_state))
        return context
