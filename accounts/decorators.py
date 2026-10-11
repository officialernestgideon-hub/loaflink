from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*allowed_roles):
    """
    Decorator that only lets users with the given roles view the page.
    Usage: @role_required('bakery')
           @role_required('bakery', 'admin')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.role not in allowed_roles:
                messages.error(request, "You don't have access to that page.")
                return redirect('accounts:redirect_by_role')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator