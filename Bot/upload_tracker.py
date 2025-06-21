# Simple global storage for pending uploads
pending_uploads = {}

def set_pending_upload(user_id: int, description: str):
    """Set a pending upload for a user"""
    pending_uploads[user_id] = description

def get_pending_upload(user_id: int) -> str:
    """Get and remove pending upload for a user"""
    return pending_uploads.pop(user_id, None)

def has_pending_upload(user_id: int) -> bool:
    """Check if user has a pending upload"""
    return user_id in pending_uploads