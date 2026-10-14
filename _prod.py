"""Full production-readiness verification."""
import os
import subprocess
import sys

ROOT = r'C:\Users\mts\Desktop\CNAM\mon_projet'
PY = r'C:\Users\mts\Desktop\CNAM\cnam\Scripts\python.exe'
sys.path.insert(0, ROOT)
os.chdir(ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mon_projet.settings')

import django
django.setup()
from django.conf import settings
from django.test import Client

fail = []

print('=== 1. Static configuration ===')
print('   STATIC_URL       =', repr(settings.STATIC_URL))
print('   STATIC_ROOT      =', settings.STATIC_ROOT)
print('   STATICFILES_DIRS =', settings.STATICFILES_DIRS)
print('   MEDIA_URL        =', repr(settings.MEDIA_URL))
print('   MEDIA_ROOT       =', settings.MEDIA_ROOT)
print('   WhiteNoise mw    =', any('whitenoise' in m.lower() for m in settings.MIDDLEWARE))
print('   STORAGES static  =', settings.STORAGES['staticfiles']['BACKEND'])
assert settings.STATIC_URL.startswith('/'), 'STATIC_URL must start with /'
if not any('whitenoise' in m.lower() for m in settings.MIDDLEWARE):
    fail.append('WhiteNoise missing')

print('')
print('=== 2. Static assets served (200 = fixed!) ===')
c = Client()
for u in ('/static/fds/style.css', '/static/fds/script.js',
          '/static/images/logo.png', '/static/fds/Feuille_text.png'):
    r = c.get(u, HTTP_HOST='localhost')
    n = len(b''.join(r.streaming_content)) if r.status_code == 200 else 0
    print('   %-34s status=%s bytes=%s' % (u, r.status_code, n))
    if r.status_code != 200:
        fail.append('static %s -> %s' % (u, r.status_code))

print('')
print('=== 3. Pages ===')
for u in ('/', '/login/'):
    r = c.get(u, HTTP_HOST='localhost')
    print('   %-9s status=%s len=%s' % (u, r.status_code, len(r.content)))
    if r.status_code != 200:
        fail.append('%s -> %s' % (u, r.status_code))

print('')
print('=== 4. {% static %} URLs in rendered homepage ===')
html = c.get('/', HTTP_HOST='localhost').content.decode('utf-8', 'ignore')
import re
for m in re.findall(r'(?:href|src)="(/static/[^"]+)"', html)[:6]:
    print('   ', m)

print('')
print('=== 5. django check ===')
r = subprocess.run([PY, 'manage.py', 'check'], capture_output=True, text=True, cwd=ROOT)
print('  ', (r.stdout or r.stderr).strip()[:200])

print('')
print('=== 6. No pending model changes ===')
r = subprocess.run([PY, 'manage.py', 'makemigrations', '--check', '--dry-run'],
                   capture_output=True, text=True, cwd=ROOT)
print('  ', (r.stdout or r.stderr).strip()[:200])

print('')
print('=' * 62)
print('FAILURES:', fail if fail else 'none')
sys.exit(1 if fail else 0)