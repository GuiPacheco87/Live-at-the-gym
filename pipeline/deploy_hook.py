import os
import urllib.request
from urllib.parse import urlparse
url=os.environ.get('VERCEL_DEPLOY_HOOK','')
parsed=urlparse(url)
if parsed.scheme!='https' or parsed.hostname!='api.vercel.com' or not parsed.path.startswith('/v1/integrations/deploy/'):
    raise SystemExit('Configure the VERCEL_DEPLOY_HOOK repository secret with a Vercel deploy hook.')
with urllib.request.urlopen(urllib.request.Request(url,data=b'',method='POST'),timeout=30) as response:
    if response.status not in (200,201):
        raise SystemExit('Vercel did not accept the deployment request')
print('Deployment requested; verify final status in Vercel.')
