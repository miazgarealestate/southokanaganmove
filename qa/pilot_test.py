"""Pilot QA for guide pages: load desktop+mobile, canonical/indexable, internal links, axe, and a test inquiry carrying the guide name to a LOCAL receiver.
Usage: python3 qa/pilot_test.py <repo_dir> [AXE_JS path]"""
import sys,os,re,shutil,subprocess,tempfile,threading,json,time,urllib.parse,socket,glob
from http.server import BaseHTTPRequestHandler,HTTPServer
from playwright.sync_api import sync_playwright
repo=sys.argv[1]; AXE=open(os.environ.get('AXE_JS','/tmp/axe/node_modules/axe-core/axe.min.js')).read()
tmp=tempfile.mkdtemp(); work=os.path.join(tmp,'site'); shutil.copytree(repo,work,ignore=shutil.ignore_patterns('.git','qa'))
def free():
    s=socket.socket();s.bind(('',0));p=s.getsockname()[1];s.close();return p
rport,sport=free(),free(); got=[]
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n=int(self.headers.get('Content-Length',0)); b=urllib.parse.parse_qs(self.rfile.read(n).decode(),keep_blank_values=True)
        got.append({k:v[0] for k,v in b.items()}); self.send_response(303); self.send_header('Location',got[-1].get('_next','/')); self.end_headers()
    def log_message(self,*a): pass
threading.Thread(target=HTTPServer(('127.0.0.1',rport),H).serve_forever,daemon=True).start()
env=dict(os.environ,FORM_ACTION=f'http://127.0.0.1:{rport}/s',FORM_NEXT=f'http://127.0.0.1:{sport}/contact/thank-you/')
subprocess.run([sys.executable,'tools/build.py'],cwd=work,env=env,check=True,stdout=subprocess.DEVNULL)
srv=subprocess.Popen([sys.executable,'-m','http.server',str(sport)],cwd=work,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
B=f'http://127.0.0.1:{sport}'; res={}
GUIDES=['guides/','guides/manufactured-homes/','guides/well-water-septic-rural-inspections/']
with sync_playwright() as p:
    br=p.chromium.launch()
    for vp,(w,h) in {'desktop':(1280,900),'mobile':(390,844)}.items():
        pg=br.new_page(viewport={'width':w,'height':h}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        for g in GUIDES:
            r=pg.goto(f'{B}/{g}'); st=r.status
            ovf=pg.evaluate('document.documentElement.scrollWidth>document.documentElement.clientWidth+1')
            can=pg.get_attribute('link[rel=canonical]','href'); robots=pg.locator('meta[name=robots]').count()
            pg.add_script_tag(content=AXE); ax=pg.evaluate("axe.run(document).then(r=>r.violations.map(v=>v.id+':'+v.nodes.length))")
            res[f'{vp}:{g}']={'status':st,'h1':pg.locator('h1').first.inner_text(),'h_overflow':ovf,'canonical':can,'canonical_ok':can=='https://southokanaganmove.ca/'+g,'noindex_meta':robots,'axe':ax}
        res[f'{vp}:js_errors']=errs; 
        if vp=='mobile': pg.screenshot(path='/tmp/mobile-guide.png',full_page=False)
        pg.close()
    # inquiry per guide
    pg=br.new_page()
    for g,slug in [(x,x.split('/')[1]) for x in GUIDES[1:]]:
        pg.goto(f'{B}/{g}'); link=pg.locator('a.btn[href^="/contact/?guide="]'); n=link.count(); link.first.click(); pg.wait_for_url('**/contact/?guide=*')
        pg.fill('#f-name','QA Test'); pg.fill('#f-email','qa@example.invalid'); pg.check('#f-consent')
        msg=pg.input_value('#f-msg'); pg.click('form.form button[type=submit]'); pg.wait_for_url('**/contact/thank-you/',timeout=5000)
        r=got[-1]; res[f'inquiry:{slug}']={'links_on_page':n,'payload_guide':r.get('guide'),'payload_title':r.get('guide_title'),'subject':r.get('_subject'),'source':r.get('source'),'prefilled_message':msg,'ok':r.get('guide')==slug and bool(r.get('guide_title'))}
    # plain contact form must keep working and carry no guide
    pg.goto(f'{B}/contact/'); pg.fill('#f-name','QA');pg.fill('#f-email','qa@example.invalid');pg.check('#f-consent');pg.click('form.form button[type=submit]');pg.wait_for_url('**/contact/thank-you/')
    res['inquiry:plain']={'guide':got[-1].get('guide'),'subject':got[-1].get('_subject')}
    # hostile param
    pg.goto(f'{B}/contact/?guide=%3Cscript%3E&t=%3Cimg%20src%3Dx%3E'); res['inquiry:hostile_param_ignored']=pg.locator('form.form input[name=guide]').input_value()==''
    br.close()
# internal links + sitemap
bad=[];files=glob.glob(work+'/**/*.html',recursive=True)
for f in files:
    for m in re.finditer(r'href="(/[^"#?]*)',open(f,encoding='utf-8').read()):
        u=m.group(1); t=os.path.join(work,u.lstrip('/'))
        if not (os.path.isfile(t) or os.path.isfile(os.path.join(t,'index.html'))): bad.append((os.path.relpath(f,work),u))
res['broken_internal_links']=sorted(set(bad))
sm=open(work+'/sitemap.xml').read(); res['sitemap_guides']=re.findall(r'<loc>(https://southokanaganmove.ca/guides/[^<]*)',sm)
srv.terminate(); shutil.rmtree(tmp)
json.dump(res,open('/tmp/pilot.json','w'),indent=1); print(json.dumps(res,indent=1)[:6000])
