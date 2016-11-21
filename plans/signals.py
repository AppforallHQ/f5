import django.dispatch

activate_subscription = django.dispatch.Signal(providing_args=["invoice"])
deactivate_subscription = django.dispatch.Signal(providing_args=["invoice"])
