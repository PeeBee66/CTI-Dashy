# sub_apps/__init__.py
from .api_search import api_search_bp
from .data_dupe import data_dupe_bp
from .folder_size import folder_size_bp
from .hash_search import hash_search_bp
from .re_send import re_send_bp
from .manifest import manifest_bp
from .settings import settings_bp
from .user_mgmt import user_mgmt_bp  

sub_app_blueprints = [
    api_search_bp, data_dupe_bp, folder_size_bp,
    hash_search_bp, re_send_bp, manifest_bp, settings_bp,
    user_mgmt_bp 
]

def register_blueprints(app, allowed_apps):
    allowed_apps_set = set(allowed_apps)
    for sub_app in sub_app_blueprints:
        if sub_app.name in allowed_apps_set:
            app.register_blueprint(sub_app)
