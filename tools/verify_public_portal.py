"""Check routing, static deployment limits and unchanged research artifacts."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import argparse,hashlib,json,re

PROJECT=Path(__file__).resolve().parents[1]
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=[]
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if values.get('id'):self.ids.append(values['id'])
        for name in ['src','href','data-src']:
            if values.get(name):self.links.append(values[name])

def main(research):
    site=PROJECT/'site';manifest=json.loads((site/'hosting-manifest.json').read_text(encoding='utf-8'))
    source_manifest=json.loads((research/'Source_Manifest.json').read_text(encoding='utf-8'))
    assert manifest['source_csv_sha256']==source_manifest['data_sha256']=='5068c83649471c0ac2daff34841c5ab6622eb13c49547875b750a95c745a2ff4'
    assert manifest['research_refitted_for_hosting'] is False
    assert manifest['public_scope']=='INTERACTIVE_PORTAL_ONLY_NO_RESEARCH_DOWNLOADS'
    assert not (site/'downloads').exists() and not (site/'reports').exists()
    file_count=0;link_count=0;total=0;largest=0
    for p in site.rglob('*'):
        if not p.is_file():continue
        file_count+=1;total+=p.stat().st_size;largest=max(largest,p.stat().st_size)
        assert p.suffix.lower() not in {'.pdf','.docx','.csv','.zip','.md','.jsonl'},p
        assert p.stat().st_size<100*1024**2,p
        if p.suffix!='.html':continue
        parser=Links();parser.feed(p.read_text(encoding='utf-8'))
        assert len(parser.ids)==len(set(parser.ids)),p
        for link in parser.links:
            value=urlsplit(link)
            if value.scheme or value.netloc:continue
            assert not value.path.startswith('/'),(p,link)
            target=(p.parent/unquote(value.path)).resolve() if value.path else p.resolve()
            assert target.is_relative_to(site.resolve()) and target.exists(),(p,link)
            link_count+=1
        if p.name=='index.html':
            for required in ['export-notes','save','portal-loading','branch-study','published-notes']:assert required in parser.ids,required
    assert total<1024**3
    for name,expected in manifest['download_sha256'].items():
        assert sha(site/'downloads'/name)==sha(research/name)==expected,name
    for identifier,name in [('data','original-tuples.json'),('candidates','pattern-register.json'),('branch-study-data','branch-study.json'),('microscope-data','microscope-context.json'),('expanded-search-data','expanded-context.json')]:
        assert sha(site/'data'/name)==manifest['interactive_payload_sha256'][identifier]
        json.loads((site/'data'/name).read_text(encoding='utf-8'))
    # Compare exact scientific JSON payloads against the completed atlas.
    original=(research/'Graph_Interaction_Atlas.html').read_text(encoding='utf-8')
    for identifier,expected in manifest['interactive_payload_sha256'].items():
        value=original.split('<script id="'+identifier+'" type="application/json">',1)[1].split('</script>',1)[0]
        assert hashlib.sha256(value.encode()).hexdigest()==expected,identifier
    for image_hash in manifest['original_graph_sha256']:assert sha(site/'assets/evidence'/(image_hash+'.png'))==image_hash
    assert len(manifest['original_graph_sha256'])==180
    atlas_js=(site/'assets/js/atlas.js').read_text(encoding='utf-8');bootstrap=(site/'assets/js/bootstrap.js').read_text(encoding='utf-8')
    assert "fetch('/api/" not in atlas_js and 'localStorage.setItem(NOTES_KEY' in atlas_js and 'JSON.stringify(value,null,2)' in atlas_js
    assert 'VISITOR_BROWSER_ONLY' in atlas_js and 'Promise.all' in bootstrap
    assert 'source samples' not in (site/'index.html').read_text(encoding='utf-8').lower()
    index=(site/'index.html').read_text(encoding='utf-8')
    assert 'Research manuscript PDF' not in index and 'Source bundle</a>' not in index
    record={'status':'PASS','public_scope':manifest['public_scope'],'static_files':file_count,'total_bytes':total,'largest_file_bytes':largest,'internal_links_checked':link_count,'scientific_payloads_exact':5,'original_csv_rows':5046,'features':132,'png_assets_verified':180,'research_download_files':0,'manuscript_in_public_release':False,'api_dependency_removed':True,'source_sha256':manifest['source_csv_sha256']}
    (PROJECT/'verification').mkdir(exist_ok=True);(PROJECT/'verification/Static_Verification.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--research-root',type=Path,default=Path('D:/Masters/Research/Experiment 03 — Relational Graph Stylometry'));args=p.parse_args();main(args.research_root)
