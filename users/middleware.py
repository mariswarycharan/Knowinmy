# from django.shortcuts import render
# from django.contrib.sessions.models import Session
# import random
# class ExceptionHandlingMiddleware:
#     """Handle uncaught exceptions instead of raising a 500.
#     """
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         return self.get_response(request)

#     def process_exception(self, request, exception):

#         if isinstance(exception, CustomMiddlewareException):
#             # Show warning in admin using Django messages framework
#             messages.warning(request, str(exception))
#             # Or you could return json for your frontend app
#             return JsonResponse({'error': str(exception)})

#         return None  # Middlewares should return None when not applied



from django.http import HttpResponse
from users.models import Tenant

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract slug from URL path
        path_parts = request.path.split('/')
        slug = path_parts[1]  # Assuming slug is the first part of the path

        try:
            tenant = Tenant.objects.get(slug=slug)
            request.tenant = tenant
        except Tenant.DoesNotExist:
            request.tenant = None

        response = self.get_response(request)
        return response
