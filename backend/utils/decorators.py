from functools import wraps

from flask import flash, redirect, session, url_for


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please login first", "error")
            return redirect(url_for("auth.login_page"))
        return view(*args, **kwargs)

    return wrapped


def profile_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("profile_complete"):
            return redirect(url_for("auth.create_profile"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Admin login required", "error")
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)

    return wrapped
