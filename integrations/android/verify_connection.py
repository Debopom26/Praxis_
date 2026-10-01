"""Real LAN HTTPS/WSS compatibility check; disposable account, no microphone."""
from pathlib import Path
import sys,ssl,secrets,json
from uuid import uuid4
from datetime import datetime,timezone
import httpx
from websockets.sync.client import connect
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import verify_deployment as deployment
trust=ssl.create_default_context(cafile=str(ROOT/'integrations/android/Praxis-Local-CA.crt'))
host='10.20.51.112'
tenant='p10-verify-phone-'+uuid4().hex[:12]
username='phone-check-'+uuid4().hex[:12]
password=secrets.token_urlsafe(32)
report={'origin':'https://'+host,'device_tested':False,'tls_verification':True}
try:
 deployment.admin(tenant,username,password)
 with httpx.Client(base_url='https://'+host,verify=trust,trust_env=False,timeout=15) as client:
  response=client.post('/api/v1/auth/login',json={'username':username,'password':password,'tenant_id':tenant})
  response.raise_for_status();value=response.json()
  assert value['token_type'].lower()=='bearer' and 31<=value['expires_in']<=1800
  headers={'Authorization':'Bearer '+value['access_token']}
  report['password_login']=True
  response=client.post('/api/v1/sessions',json={'tenant_id':tenant,'call_id':'connection-check','host_app_id':'praxis-caller','created_at':datetime.now(timezone.utc).isoformat()},headers=headers)
  response.raise_for_status();sid=response.json()['session_id'];report['session_created']=True
  with connect('wss://'+host+'/api/v1/stream/'+sid,ssl=trust,additional_headers=headers,proxy=None,open_timeout=15) as ws:
   hello=json.loads(ws.recv(timeout=10));assert hello['type']=='connection' and hello['session_id']==sid
   report['authenticated_wss_hello']=True
  client.post('/api/v1/sessions/'+sid+'/end',headers=headers).raise_for_status()
  report['session_ended']=True
finally:
 deployment.cleanup([tenant]);report['temporary_account_removed']=True
(ROOT/'integrations/android/connection-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
