"""Génère les pages fr / en / ar indexables à partir de index.html (source française)."""
import re, json, subprocess, html, os, sys
REPO=sys.argv[1]
BASE='https://username100-ch.github.io/vtc-versailles/'   # à remplacer par le nom de domaine définitif
src=open(os.path.join(REPO,'_source','index.html')).read()
js=src[src.index('var T={'):src.index('var IDX=')]
data=json.loads(subprocess.check_output(['node','-e',js+'process.stdout.write(JSON.stringify({T:T,PH:PH}))']))
T,PH=data['T'],data['PH']
IDX={'fr':0,'en':1,'ar':2}
URL={'fr':BASE,'en':BASE+'en/','ar':BASE+'ar/'}
META={
'fr':dict(title="Chauffeur VTC à Versailles et Paris | Carrosse VTC",
  desc="Chauffeur privé VTC à Versailles, disponible dans toute l'Île-de-France 24h/24 : aéroports Roissy-CDG et Orly, palaces parisiens (George V, Plaza Athénée, Peninsula), Paris, Tour Eiffel, Disneyland, Château de Versailles. Prix fixe, réservation par WhatsApp.",
  og="fr_FR"),
'en':dict(title="Private Driver in Paris & Versailles | Chauffeur Service | Carrosse VTC",
  desc="Private chauffeur in Paris and Versailles, 24/7: airport transfers from Charles de Gaulle and Orly, Paris palace hotels (George V, Plaza Athénée, Peninsula), shopping on the Champs-Élysées, Disneyland and Palace of Versailles tours. Fixed price, book on WhatsApp.",
  og="en_GB"),
'ar':dict(title="سائق خاص في باريس وفرساي | ليموزين وتوصيل من المطار | كاروس VTC",
  desc="سائق خاص في باريس وفرساي على مدار الساعة: استقبال وتوصيل من مطار شارل ديغول وأورلي إلى فنادق باريس الفاخرة (جورج الخامس، بلازا أثينيه، بينينسولا)، جولات تسوق في الشانزليزيه، ديزني لاند وقصر فرساي. سيارة مع سائق للعائلات بسعر ثابت، والحجز عبر واتساب.",
  og="ar_AR"),
}
def head_tags(l):
    m=META[l]
    alts=''.join(f'<link rel="alternate" hreflang="{k}" href="{URL[k]}">\n' for k in ('fr','en','ar'))
    alts+=f'<link rel="alternate" hreflang="x-default" href="{URL["en"]}">\n'
    ld={"@context":"https://schema.org","@type":"LocalBusiness","@id":BASE+"#business",
        "name":"Carrosse VTC","url":URL[l],"image":BASE+"images/hero-galerie-des-glaces.jpg",
        "description":m['desc'],"telephone":"+33600000000","priceRange":"€€",
        "address":{"@type":"PostalAddress","addressLocality":"Versailles","postalCode":"78000","addressRegion":"Île-de-France","addressCountry":"FR"},
        "areaServed":[{"@type":"AdministrativeArea","name":"Île-de-France"},{"@type":"City","name":"Paris"},{"@type":"City","name":"Versailles"}],
        "openingHoursSpecification":{"@type":"OpeningHoursSpecification","dayOfWeek":["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],"opens":"00:00","closes":"23:59"},
        "makesOffer":[{"@type":"Offer","itemOffered":{"@type":"Service","name":n}} for n in ("Airport transfer CDG Orly","Paris palace hotel transfers","Paris chauffeur service","Disneyland Paris transfer","Versailles Palace tour")]}
    return (f'<title>{html.escape(m["title"])}</title>\n'
            f'<meta name="description" content="{html.escape(m["desc"])}">\n'
            f'<link rel="canonical" href="{URL[l]}">\n'+alts+
            f'<meta property="og:type" content="website">\n<meta property="og:site_name" content="Carrosse VTC">\n'
            f'<meta property="og:title" content="{html.escape(m["title"])}">\n<meta property="og:description" content="{html.escape(m["desc"])}">\n'
            f'<meta property="og:url" content="{URL[l]}">\n<meta property="og:image" content="{BASE}images/hero-galerie-des-glaces.jpg">\n<meta property="og:locale" content="{m["og"]}">\n'
            f'<meta name="twitter:card" content="summary_large_image">\n'
            f'<script type="application/ld+json">{json.dumps(ld,ensure_ascii=False)}</script>\n')
def render(l):
    s=src
    # en-tête : on remplace description + title par le bloc SEO de la langue
    s=re.sub(r'<meta name="description"[^>]*>\n','',s,count=1)
    s=re.sub(r'<title>.*?</title>\n',lambda _:head_tags(l),s,count=1)
    s=s.replace('<html lang="fr">',f'<html lang="{l}" dir="{"rtl" if l=="ar" else "ltr"}" data-lang="{l}" data-page-lang="{l}">',1)
    # sélecteur de langue : vrais liens
    rel={'fr':{'fr':'./','en':'en/','ar':'ar/'},'en':{'fr':'../','en':'./','ar':'../ar/'},'ar':{'fr':'../','en':'../en/','ar':'./'}}[l]
    def lk(c,label):
        cur=' aria-current="page"' if c==l else ''
        return f'<a href="{rel[c]}" data-l="{c}" lang="{c}" hreflang="{c}"{cur}>{label}</a>'
    s=re.sub(r'<button type="button" data-l="fr"[^>]*>FR</button>\s*<button type="button" data-l="en"[^>]*>EN</button>\s*<button type="button" data-l="ar"[^>]*>عربي</button>',
             lambda _:lk('fr','FR')+'\n        '+lk('en','EN')+'\n        '+lk('ar','عربي'),s,count=1)
    # textes traduits
    if l!='fr':
        i=IDX[l]-1
        def sub(m):
            k=m.group(3)
            if k not in T: return m.group(0)
            return m.group(1)+html.escape(T[k][i],quote=False)+m.group(5)
        s=re.sub(r'(<(\w+)\b[^>]*\bdata-t="([^"]+)"[^>]*>)((?:(?!</\2>).)*?)(</\2>)',sub,s,flags=re.S)
        for idk,vals in PH.items():
            s=re.sub(r'(<(?:input|textarea)[^>]*\bid="%s"[^>]*?)(\s*(?:required)?>)'%re.escape(idk),lambda m:m.group(1)+f' placeholder="{html.escape(vals[IDX[l]])}"'+m.group(2),s,count=1)
        s=s.replace('src="images/','src="../images/').replace('url("images/','url("../images/')
    return s
out={'fr':'index.html','en':'en/index.html','ar':'ar/index.html'}
for l,p in out.items():
    os.makedirs(os.path.dirname(os.path.join(REPO,p)) or REPO,exist_ok=True)
    open(os.path.join(REPO,p),'w').write(render(l))
sm=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for l in ('fr','en','ar'):
    sm.append(f'  <url><loc>{URL[l]}</loc>')
    for k in ('fr','en','ar'): sm.append(f'    <xhtml:link rel="alternate" hreflang="{k}" href="{URL[k]}"/>')
    sm.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{URL["en"]}"/>')
    sm.append('  </url>')
sm.append('</urlset>')
open(os.path.join(REPO,'sitemap.xml'),'w').write('\n'.join(sm)+'\n')
open(os.path.join(REPO,'robots.txt'),'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n')
print('pages générées')
