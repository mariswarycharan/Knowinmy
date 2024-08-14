from django.shortcuts import render
from django.contrib.sessions.models import Session
import random

def idempotent_post_middleware(get_response):
    def middleware(request):
        if not request.session.__contains__('idempo_token'):
            request.session.__setitem__('idempo_token', [])
        response = get_response(request)
        return response
    return middleware
