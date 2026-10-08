"""Deterministic AC02-AC08 smoke demonstration for the candidate build."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient
from app.main import app

def main():
    with TestClient(app) as client:
        login = client.post('/api/auth/login', data={'username':'admin','password':'Admin@12345'})
        login.raise_for_status(); h={'Authorization':'Bearer '+login.json()['access_token']}
        def post(path,payload=None,ok=(200,201,409)):
            r=client.post(path,json=payload or {},headers=h); print(f'{path}: {r.status_code}')
            if r.status_code not in ok: r.raise_for_status()
            return r
        def ensure(path,payload): return post(path,payload)
        ensure('/api/books',{'accession_no':'AC-DEMO-01','title':'Acceptance Book','author':'AISYS','category':'Test'})
        ensure('/api/members',{'member_no':'AC-M-01','name':'Acceptance Member','email':'ac@example.local'})
        ensure('/api/rfid/associate',{'accession_no':'AC-DEMO-01','tag_id':'AC-RFID-01'})
        # If an earlier run left an active loan, finish it first.
        post('/api/circulation/checkin',{'accession_no':'AC-DEMO-01','protocol':'NCIP2'},ok=(200,409))
        post('/api/circulation/checkout',{'member_no':'AC-M-01','accession_no':'AC-DEMO-01','protocol':'NCIP2','days':14})
        post('/api/circulation/renew',{'accession_no':'AC-DEMO-01','protocol':'SIP2','days':7})
        post('/api/circulation/checkin',{'accession_no':'AC-DEMO-01','protocol':'NCIP2'})
        post('/api/rfid/read',{'tag_id':'AC-RFID-01','shelf':'A-01','expected_shelf':'A-01'})
        post('/api/gate/event',{'tag_id':'AC-RFID-01','security_bit':True,'cctv_ref':'mock://cctv/ac06'})
        card=client.post('/api/smart-card/login',json={'card_id':'CARD-ADMIN-01','username':'admin'},headers=h); print('/api/smart-card/login:',card.status_code); card.raise_for_status()
        operator_login=client.post('/api/auth/login',data={'username':'operator','password':'Operator@12345'}); operator_login.raise_for_status(); oh={'Authorization':'Bearer '+operator_login.json()['access_token']}
        denied=client.post('/api/admin/config',json={'key':'acceptance','value':'denied'},headers=oh); print('/api/admin/config as operator:',denied.status_code); assert denied.status_code==403
        print('Dashboard:',client.get('/api/dashboard',headers=h).json())
        print('Circulation rows:',len(client.get('/api/reports/circulation',headers=h).json()))
        print('Audit rows:',len(client.get('/api/audit',headers=h).json()))
        print('AC02-AC08 acceptance smoke completed.')
if __name__=='__main__': main()
