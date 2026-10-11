from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """Only allow platform admins (role='admin' or is_superuser)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not (request.user.is_superuser or request.user.role == 'admin'):
            messages.error(request, "You don't have access to that page.")
            return redirect('accounts:redirect_by_role')
        return view_func(request, *args, **kwargs)
    return wrapper