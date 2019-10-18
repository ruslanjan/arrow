from django.utils.deprecation import MiddlewareMixin


class InitializeProblemsetProfile(MiddlewareMixin):

    def process_request(self, request):
        pass