from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import os,sqlite3,json,hashlib,secrets,hmac,time,base64
from http.cookies import SimpleCookie
from datetime import date
ROOT=Path(__file__).resolve().parent;os.chdir(ROOT/'site');DB=ROOT/'campus.sqlite';sessions={}
def db():
 d=sqlite3.connect(DB);d.row_factory=sqlite3.Row;return d
def pw(p,s):return hashlib.pbkdf2_hmac('sha256',p.encode(),s.encode(),180000).hex()
d=db();d.executescript('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name,email,role,reg,salt,hash);CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY,student INTEGER,title,grp INTEGER,points INTEGER,status,date,notes,filename,mime,data BLOB);');names=['Anjali Menon','Aarav Nair','Ananya S','Arjun Thomas','Diya Krishna','Fathima Basheer','Govind R','Meera Nair','Neha Joseph'];
if not d.execute('select count(*) from users').fetchone()[0]:
 for i,n in enumerate(names):
  s=secrets.token_hex(16);d.execute('insert into users values(?,?,?,?,?,?,?)',(i+1,n,n.split()[0].lower()+'@campus.edu','teacher' if not i else 'student','Faculty advisor' if not i else f'NSS24CS{i:03}',s,pw('Campus2024!',s)))
  if i:
   for g,t in enumerate(['Intercollege arts festival','Technical paper presentation','Prototype showcase']):d.execute('insert into records(student,title,grp,points,status,date,notes) values(?,?,?,?,?,?,?)',(i+1,t,g,[40,32,24,20][(i+g)%4],'Pending' if (i+g)%5==0 else 'Approved',f'2026-10-{10+i:02}','Sample activity for the preview.'))
 d.commit()
d.execute("create table if not exists workspaces(user integer primary key, content text)")
if 'ruleRef' not in [col[1] for col in d.execute('pragma table_info(records)')]:d.execute("alter table records add column ruleRef text default ''")
d.executescript('CREATE TABLE IF NOT EXISTS resources(id INTEGER PRIMARY KEY,owner INTEGER,filename TEXT,mime TEXT,data BLOB,day TEXT); CREATE TABLE IF NOT EXISTS notices(id INTEGER PRIMARY KEY,owner INTEGER,recipient INTEGER,title TEXT,body TEXT,day TEXT);')
if 'feedback' not in [col[1] for col in d.execute('pragma table_info(records)')]:d.execute("alter table records add column feedback text default ''")
d.execute('CREATE TABLE IF NOT EXISTS activity_events(id INTEGER PRIMARY KEY,record INTEGER,actor TEXT,kind TEXT,at TEXT,note TEXT,points INTEGER,grp INTEGER)');d.execute('CREATE INDEX IF NOT EXISTS event_record ON activity_events(record,id)');d.commit();d.close();opened=set()
def log_event(d,id,u,kind,note='',points=None,grp=None):
 d.execute("insert into activity_events(record,actor,kind,at,note,points,grp) values(?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),?,?,?)",(id,u['name'],kind,note,points,grp))
class H(SimpleHTTPRequestHandler):
 def reply(self,j,n=200,c=None):
  self.send_response(n);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');
  if c:self.send_header('Set-Cookie',c)
  self.end_headers();self.wfile.write(json.dumps(j).encode())
 def token(self):
  if self.headers.get('X-Campus-Session'):return self.headers['X-Campus-Session']
  auth=self.headers.get('Authorization','')
  if auth.startswith('Bearer '):return auth[7:]
  ck=SimpleCookie(self.headers.get('Cookie',''));t=ck.get('session');return t.value if t else ''
 def user(self):return sessions.get(self.token())
 def do_GET(self):
  if not self.path.startswith('/api/'):return super().do_GET()
  u=self.user();
  if not u:return self.reply({'error':'Sign in to continue'},401)
  with db() as d:
   if self.path=='/api/notices':return self.reply([dict(r) for r in d.execute("select id,title,body,recipient,day from notices where (?='teacher' and owner=?) or (?='student' and (recipient=0 or recipient=?)) order by id desc",(u['role'],u['id'],u['role'],u['id']))])
   if self.path=='/api/resources':return self.reply([dict(r) for r in d.execute('select id,filename,mime,day from resources where owner=? order by id desc',(u['id'],))])
   if self.path.startswith('/api/resource/'):
    f=d.execute('select * from resources where id=? and owner=?',(self.path.split('/')[-1],u['id'])).fetchone()
    if not f:return self.reply({'error':'File unavailable'},404)
    self.send_response(200);self.send_header('Content-Type',f['mime']);self.send_header('Content-Disposition','attachment');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(f['data']);return
   if self.path=='/api/workspace':
    w=d.execute('select content from workspaces where user=?',(u['id'],)).fetchone();return self.reply(json.loads(w[0]) if w else {'notes':'','pins':[]})
   if self.path=='/api/state':return self.reply({'me':u,'students':[dict(r) for r in d.execute("select id,name,email,reg from users where role='student' and (?='teacher' or id=?)",(u['role'],u['id']))],'records':[dict(r,history=[dict(e) for e in d.execute('select actor,kind,at,note,points,grp from activity_events where record=? order by id',(r['id'],))]) for r in d.execute("select id,student,title,grp,points,status,date,notes,feedback,filename,mime,ruleRef from records where ?='teacher' or student=? order by id desc",(u['role'],u['id']))]})
   r=d.execute("select * from records where id=? and (?='teacher' or student=?)",(self.path.split('/')[-1],u['role'],u['id'])).fetchone();
   if not r or not r['data']:return self.reply({'error':'No attachment'},404)
   opened.add((self.token(),r['id'],hashlib.sha256(r['data']).digest()));self.send_response(200);self.send_header('Cache-Control','no-store');self.send_header('Content-Type',r['mime']);self.send_header('Content-Disposition','attachment; filename="certificate.'+{'application/pdf':'pdf','image/png':'png','image/jpeg':'jpg'}[r['mime']]+'"');self.end_headers();self.wfile.write(r['data'])
 def do_POST(self):
  try:
   n=int(self.headers.get('Content-Length',0));assert n<4300000,'File too large';a=json.loads(self.rfile.read(n));u=self.user()
   with db() as d:
    if self.path=='/api/login':
     r=d.execute('select * from users where email=? and role=?',(a['email'].strip().lower(),a['role'])).fetchone();
     if not r or not hmac.compare_digest(pw(a['password'],r['salt']),r['hash']):return self.reply({'error':'Check your email, password and selected role.'},401)
     tok=secrets.token_urlsafe(32);sessions[tok]={k:r[k] for k in ['id','name','email','role','reg']};return self.reply({'token':tok},c=f'session={tok}; Path=/; HttpOnly; Secure; SameSite=None; Partitioned')
    if not u:return self.reply({'error':'Please sign in'},401)
    if self.path=='/api/workspace':
     w={'notes':str(a['notes'])[:6000],'pins':[int(i) for i in a['pins'][:2000]]};d.execute('insert or replace into workspaces values(?,?)',(u['id'],json.dumps(w)));return self.reply({})
    if self.path=='/api/publish' and u['role']=='teacher':
     recipient=int(a['recipient']);assert recipient==0 or d.execute("select 1 from users where role='student' and id=?",(recipient,)).fetchone();assert a['title'].strip() and a['body'].strip();d.execute('insert into notices(owner,recipient,title,body,day) values(?,?,?,?,CURRENT_DATE)',(u['id'],recipient,a['title'].strip()[:120],a['body'].strip()[:2000]));return self.reply({})
    if self.path=='/api/upload-resource' and u['role']=='teacher':
     assert a['mime'] in ('application/pdf','image/jpeg','image/png');raw=base64.b64decode(a['file'],validate=True);assert 0<len(raw)<=3145728;d.execute('insert into resources(owner,filename,mime,data,day) values(?,?,?,?,CURRENT_DATE)',(u['id'],a['filename'][:120],a['mime'],raw));return self.reply({})
    if self.path=='/api/logout':sessions.pop(self.token(),None);return self.reply({},c='session=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=None; Partitioned')
    if self.path=='/api/review' and u['role']=='teacher':
     d.execute('begin immediate');r=d.execute("select * from records where id=? and status='Pending'",(int(a['id']),)).fetchone()
     if not r:return self.reply({'error':'This submission has already been reviewed.'},409)
     if a['status']=='Approved':
      if not r['data'] or (self.token(),r['id'],hashlib.sha256(r['data']).digest()) not in opened:return self.reply({'error':'Open the submitted proof before awarding points.'},400)
      catalog=json.loads((ROOT/'site/award-rules.json').read_text());key=a.get('ruleRef');rule=catalog.get(key)
      if not rule or a.get('confirmed') is not True:return self.reply({'error':'Select and confirm a supported handbook rule.'},400)
      grp,rate,cap,head=rule
      if key=='3.17':
       if type(a.get('hours')) is not int or a['hours']<1:return self.reply({'error':'Enter verified approved course hours.'},400)
       rate=a['hours']
      previous=sum(x['points'] for x in d.execute("select points,ruleRef from records where student=? and status='Approved'",(r['student'],)) if catalog.get(x['ruleRef'],[None]*4)[3]==head);group_total=d.execute("select coalesce(sum(points),0) from records where student=? and status='Approved' and grp=?",(r['student'],grp)).fetchone()[0];amount=min(rate,max(0,cap-previous),max(0,40-group_total))
      if a.get('points')!=amount:return self.reply({'error':'Prior awards changed. Refresh and confirm the recalculated points.'},409)
      d.execute("update records set status='Approved',points=?,grp=?,ruleRef=?,feedback=? where id=?",(amount,grp,key,a['notes'][:1500],r['id']))
     elif a['status']=='Correction requested' and a['notes'].strip():d.execute("update records set status=?,feedback=? where id=?",(a['status'],a['notes'][:1500],r['id']))
     else:return self.reply({'error':'Enter the clarification needed.'},400)
     log_event(d,r['id'],u,a['status'],a['notes'][:1500],amount if a['status']=='Approved' else None,grp if a['status']=='Approved' else None)
    elif self.path=='/api/submit' and u['role']=='student':
     if not str(a.get('title') or '').strip() or str(a.get('grp')) not in ('0','1','2') or str(a.get('points')) not in {str(i) for i in range(1,41)} or not a.get('date') or not a.get('filename') or not a.get('file'):return self.reply({'error':'Title, group, date, whole requested points (1–40) and a certificate are required.'},400)
     if date.fromisoformat(a['date']).isoformat()!=a['date']:return self.reply({'error':'Enter a valid activity date.'},400)
     assert a['mime'] in ('application/pdf','image/png','image/jpeg');data=base64.b64decode(a['file'],validate=True);assert 0<len(data)<=3*1024*1024
     vals=(a['title'][:150],int(a['grp']),int(a['points']),'Pending',a['date'],str(a.get('notes') or '')[:1500],a['filename'][:120],a['mime'],data,str(a.get('ruleRef',''))[:12],u['id']);
     if a.get('id'):
      updated=d.execute("update records set title=?,grp=?,points=?,status=?,date=?,notes=?,filename=?,mime=?,data=?,ruleRef=? where student=? and id=? and status='Correction requested'",vals+(int(a['id']),))
      if updated.rowcount!=1:return self.reply({'error':'This submission is no longer awaiting correction. Reload your portfolio.'},409)
     else:created=d.execute('insert into records(title,grp,points,status,date,notes,filename,mime,data,ruleRef,student) values(?,?,?,?,?,?,?,?,?,?,?)',vals)
     log_event(d,int(a['id']) if a.get('id') else created.lastrowid,u,'Resubmitted' if a.get('id') else 'Submitted')
    else:return self.reply({'error':'Not permitted'},403)
   return self.reply({})
  except Exception:return self.reply({'error':'Please check the form and file size.'},400)
ThreadingHTTPServer(('127.0.0.1',int(os.environ.get('PORT','8003'))),H).serve_forever()
