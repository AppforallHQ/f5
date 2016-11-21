from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from importlib import import_module



class TokenSessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        engine = import_module(settings.SESSION_ENGINE)
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)
        print "Session key:",session_key
        request.session = engine.SessionStore(session_key)
        if not request.session.exists(request.session.session_key):
            session_key = request.POST.get("token",None)
            request.session = engine.SessionStore(session_key)
            print "Key From Token",request.session.items()
            if not request.session.exists(request.session.session_key):   
                request.session.create() 