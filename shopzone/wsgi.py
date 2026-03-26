"""
WSGI config for shopzone project (Render deployment proxy).

Delegates to actual ecomm project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopzone.ecomm.settings')

application = get_wsgi_application()
