"""
Middleware OBLIGATOIRE : attache request.tenant pour chaque requête d'un
utilisateur connecté. Toutes les vues internes filtrent leurs querysets par
request.tenant pour garantir qu'un tenant ne voit jamais les données d'un autre.
"""


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None
        if request.user.is_authenticated and getattr(request.user, "tenant_id", None):
            request.tenant = request.user.tenant
        return self.get_response(request)
