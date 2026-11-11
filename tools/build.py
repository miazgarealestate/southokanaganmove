#!/usr/bin/env python3
"""Static build for southokanaganmove.ca.
Reads content/*.html (front matter + HTML fragment), writes clean-URL pages, sitemap.xml and 404.html.
Run:  python3 tools/build.py
"""
import os, re, json, html, datetime
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://southokanaganmove.ca'
TODAY = datetime.date.today().isoformat()
OG_DEFAULT = 'images/vineyard-escarpment-lake-wide.jpg'

NAV = [
    ('/moving-to-south-okanagan/', 'Moving here'),
    ('/living-in-osoyoos/', 'Osoyoos'),
    ('/living-in-oliver/', 'Oliver'),
    ('/living-on-anarchist-mountain/', 'Anarchist Mountain'),
    ('/buying-rural-property-bc/', 'Rural property'),
    ('/buying-home-south-okanagan/', 'Buying'),
    ('/about/', 'About Pat'),
]
FOOT = NAV + [('/osoyoos-vs-oliver/', 'Osoyoos vs. Oliver'),
              ('/moving-from-vancouver-to-south-okanagan/', 'Moving from Vancouver'),
              ('/contact/', 'Contact'), ('/privacy.html', 'Privacy notice')]


def esc(s):
    return html.escape(s, quote=True)


_img_cache = {}


def img(name, alt, sizes='(max-width:900px) 100vw, 560px', cls='', eager=False):
    """Responsive <img> with width/height; makes a 640w copy in images/s/."""
    src = f'images/{name}.jpg'
    path = os.path.join(ROOT, src)
    im = Image.open(path)
    w, h = im.size
    small = f'images/s/{name}-640.jpg'
    sp = os.path.join(ROOT, small)
    if not os.path.exists(sp):
        c = im.convert('RGB')
        c.thumbnail((640, 640 * 2))
        c.save(sp, quality=78, optimize=True)
    sw, sh = Image.open(sp).size
    load = 'eager" fetchpriority="high' if eager else 'lazy'
    c = f' class="{cls}"' if cls else ''
    return (f'<img{c} src="/{src}" srcset="/{small} {sw}w, /{src} {w}w" sizes="{sizes}" '
            f'width="{w}" height="{h}" alt="{esc(alt)}" loading="{load}" decoding="async"/>')


FORM = '''<form class="form" action="https://formspree.io/f/xzdqkvra" method="POST">
<input type="hidden" name="_subject" value="southokanaganmove.ca inquiry"/>
<input type="hidden" name="source" value="southokanaganmove.ca"/>
<input type="hidden" name="_next" value="https://southokanaganmove.ca/contact/thank-you/"/>
<div class="hp" aria-hidden="true"><label>Leave this field empty<input type="text" name="_gotcha" tabindex="-1" autocomplete="off"/></label></div>
<div class="field"><label for="f-name">Name</label><input id="f-name" name="name" type="text" autocomplete="name" required/></div>
<div class="row">
<div class="field"><label for="f-email">Email</label><input id="f-email" name="email" type="email" autocomplete="email" required/></div>
<div class="field"><label for="f-phone">Phone <span class="opt">(optional)</span></label><input id="f-phone" name="phone" type="tel" autocomplete="tel"/></div>
</div>
<div class="row">
<div class="field"><label for="f-area">Area of interest</label><select id="f-area" name="area_of_interest">
<option value="">Select one</option><option>Osoyoos</option><option>Oliver</option><option>Anarchist Mountain</option><option>Other South Okanagan community</option><option>Not sure yet</option></select></div>
<div class="field"><label for="f-time">Relocation timeframe</label><select id="f-time" name="timeframe">
<option value="">Select one</option><option>Within 3 months</option><option>3 to 6 months</option><option>6 to 12 months</option><option>More than a year</option><option>Just researching</option></select></div>
</div>
<div class="field"><label for="f-msg">Message</label><textarea id="f-msg" name="message" placeholder="Where are you now, what are you looking for, and what would help most?"></textarea></div>
<div class="consent"><input id="f-consent" name="consent" type="checkbox" value="yes" required/>
<label for="f-consent">I agree that Pat Miazga may contact me by email or phone about my inquiry. I can withdraw my consent at any time. See the <a href="/privacy.html">privacy notice</a>.</label></div>
<button class="btn" type="submit">Send message</button>
<p class="note">Your message is sent to Pat through Formspree, a third-party form service. See the <a href="/privacy.html">privacy notice</a>.</p>
</form>'''


def expand(fragment):
    def rep(m):
        parts = [p.strip() for p in m.group(1).split('|')]
        name, alt = parts[0], parts[1]
        sizes = parts[2] if len(parts) > 2 and parts[2] else '(max-width:900px) 100vw, 760px'
        eager = len(parts) > 3 and parts[3] == 'eager'
        return img(name, alt, sizes, eager=eager)
    fragment = re.sub(r'\{\{img:([^}]+)\}\}', rep, fragment)
    return fragment.replace('{{form}}', FORM)


def parse(path):
    raw = open(path, encoding='utf-8').read()
    head, body = raw.split('\n---\n', 1)
    meta = {}
    for line in head.strip().splitlines():
        k, v = line.split(':', 1)
        meta[k.strip()] = v.strip()
    meta['body'] = expand(body)
    return meta


def header(current):
    items = ''.join(
        f'<li><a href="{u}"{" aria-current=\"page\"" if u == current else ""}>{esc(t)}</a></li>' for u, t in NAV)
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap bar">
<a class="brand" href="/">South Okanagan <span>Move</span></a>
<button class="nav-toggle" type="button" aria-expanded="false" aria-controls="nav">Menu</button>
<nav id="nav" aria-label="Main"><ul>{items}</ul></nav>
<a class="btn btn-sm" href="/contact/">Ask Pat</a>
</div></header>'''


def footer():
    links = ''.join(f'<li><a href="{u}">{esc(t)}</a></li>' for u, t in FOOT)
    return f'''<footer class="site-footer"><div class="wrap">
<div class="grid">
<div><p class="brand" style="margin-bottom:.5em">South Okanagan Move</p>
<p>Practical guidance for buying property, relocating, and building a life in the South Okanagan.</p></div>
<div><h2>Explore</h2><ul>{links}</ul></div>
<div><h2>Contact</h2><p>Pat Miazga, REALTOR®<br/>Phone: <a href="tel:+16045625982">604-562-5982</a></p>
<p><a class="btn btn-sm" href="/contact/">Planning a move? Ask Pat.</a></p></div>
</div>
<div class="legal">
<p class="disclosure"><strong>Pat Miazga, REALTOR®</strong> &middot; <strong>eXp Realty</strong> (eXp Realty of Canada, Inc.)</p>
<p>Information on this website is general in nature and is not legal, tax, financial or engineering advice. Confirm details with the relevant authority or a qualified professional before relying on them.</p>
</div></div></footer>'''


def jsonld(meta, url):
    graph = []
    if meta['slug'] == 'home':
        graph += [
            {"@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/", "name": "South Okanagan Move",
             "publisher": {"@id": SITE + "/#org"}},
            {"@type": "Organization", "@id": SITE + "/#org", "name": "South Okanagan Move", "url": SITE + "/"},
            {"@type": "Person", "@id": SITE + "/#pat", "name": "Pat Miazga", "jobTitle": "REALTOR®",
             "url": SITE + "/about/", "knowsLanguage": ["English", "Polish"],
             "worksFor": {"@type": "Organization", "name": "eXp Realty of Canada, Inc."}},
        ]
    else:
        crumbs = [("Home", SITE + "/")]
        if meta.get('parent'):
            pu, pt = meta['parent'].split('|')
            crumbs.append((pt, SITE + pu))
        crumbs.append((meta['crumb'], url))
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(crumbs)]})
        if meta['slug'] == 'about':
            graph.append({"@type": "Person", "@id": SITE + "/#pat", "name": "Pat Miazga", "jobTitle": "REALTOR®",
                          "url": url, "knowsLanguage": ["English", "Polish"],
                          "worksFor": {"@type": "Organization", "name": "eXp Realty of Canada, Inc."}})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)


def page(meta):
    slug = meta['slug']
    if slug == 'home':
        url, out, cur = SITE + '/', 'index.html', '/'
    else:
        out = meta.get('out') or f'{slug}/index.html'
        url = SITE + ('/' + out if out.endswith('.html') else f'/{slug}/')
        cur = '/' + slug + '/' if not meta.get('out') else '/' + out
    og = meta.get('image') or OG_DEFAULT
    noindex = '<meta name="robots" content="noindex,follow"/>\n' if meta.get('noindex') == 'yes' else ''
    ld = '' if meta.get('noindex') == 'yes' else f'<script type="application/ld+json">{jsonld(meta, url)}</script>\n'
    title = meta['title']
    if slug == 'home':
        main_open = '<main id="main">'
        top = ''
    else:
        parent = ''
        if meta.get('parent'):
            pu, pt = meta['parent'].split('|')
            parent = f'<li><a href="{pu}">{esc(pt)}</a></li>'
        crumbs = f'<nav class="crumbs" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li>{parent}<li aria-current="page">{esc(meta["crumb"])}</li></ol></nav>'
        lede = f'<p class="lede">{meta["lede"]}</p>' if meta.get('lede') else ''
        top = f'<div class="wrap">{crumbs}<div class="page-head"><h1>{meta["h1"]}</h1>{lede}</div></div>'
        main_open = '<main id="main">'
    body = meta['body']
    cta = ''
    if meta.get('cta', 'yes') == 'yes' and slug not in ('home', 'contact'):
        cta = '''<div class="cta-band"><div class="wrap"><div><h2>Planning a move? Ask Pat.</h2>
<p>Tell me where you are in the process. No pressure, no obligation.</p></div>
<a class="btn" href="/contact/">Ask Pat</a></div></div>'''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{esc(title)}</title>
<meta name="description" content="{esc(meta['description'])}"/>
<link rel="canonical" href="{url}"/>
{noindex}<meta property="og:type" content="website"/>
<meta property="og:site_name" content="South Okanagan Move"/>
<meta property="og:title" content="{esc(meta.get('og_title', title))}"/>
<meta property="og:description" content="{esc(meta['description'])}"/>
<meta property="og:url" content="{url}"/>
<meta property="og:image" content="{SITE}/{og}"/>
<meta name="twitter:card" content="summary_large_image"/>
<link rel="preload" href="/assets/fonts/manrope-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin/>
<link rel="stylesheet" href="/assets/css/brand.css"/>
<link rel="stylesheet" href="/assets/css/site.css"/>
{ld}</head>
<body>
{header(cur)}
{main_open}
{top}
{body}
{cta}
</main>
{footer()}
<script src="/assets/js/site.js" defer></script>
</body>
</html>
''', out, url


def main():
    cdir = os.path.join(ROOT, 'content')
    pages = []
    for f in sorted(os.listdir(cdir)):
        if not f.endswith('.html'):
            continue
        meta = parse(os.path.join(cdir, f))
        text, out, url = page(meta)
        dest = os.path.join(ROOT, out)
        os.makedirs(os.path.dirname(dest) or ROOT, exist_ok=True)
        open(dest, 'w', encoding='utf-8').write(text)
        if meta.get('noindex') != 'yes' and meta['slug'] != '404':
            pages.append((url, meta.get('updated', TODAY), 1.0 if meta['slug'] == 'home' else 0.8))
        print('built', out)
    pages.sort(key=lambda p: (p[0] != SITE + '/', p[0]))
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u, d, p in pages:
        sm += f'  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n'
    sm += '</urlset>\n'
    open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write(sm)
    print(len(pages), 'URLs in sitemap')


if __name__ == '__main__':
    main()
