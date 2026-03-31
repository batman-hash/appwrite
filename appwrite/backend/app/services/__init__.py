"""Service layer for the modular backend."""

from backend.app.services.auth_service import (
    activate_user,
    authenticate_user,
    current_user_payload,
    logout_user,
    register_user,
    request_password_reset,
)
from backend.app.services.track_service import (
    create_project,
    create_track,
    get_project,
    get_track,
    list_builtin_tracks,
    list_projects,
    list_tracks,
)
from backend.app.services.upload_service import (
    create_shared_file,
    create_shared_file_from_upload,
    list_shared_files,
)
from backend.app.services.user_service import (
    get_user_email_history,
    list_recent_users,
    send_user_email,
    sync_users_to_subscribers,
)

__all__ = [
    "activate_user",
    "authenticate_user",
    "current_user_payload",
    "create_project",
    "create_shared_file",
    "create_shared_file_from_upload",
    "create_track",
    "get_project",
    "get_track",
    "get_user_email_history",
    "list_builtin_tracks",
    "list_projects",
    "list_recent_users",
    "list_shared_files",
    "list_tracks",
    "logout_user",
    "register_user",
    "request_password_reset",
    "send_user_email",
    "sync_users_to_subscribers",
]

