"""Convert the completed, reviewed atlas to a static GitHub Pages portal."""
from __future__ import annotations
import argparse,base64,hashlib,html,json,re,shutil
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit

PROJECT=Path(__file__).resolve().parents[1]
RESOURCE_ROUTES={
 '/branch-record':'Branch_Geometry_Study.json','/branch-features':'Branch_Synthetic_Features.csv',
 '/branch-sensitivity':'Branch_Geometry_Features.csv','/branch-parameters':'Branch_Geometry_Parameters.zip',
 '/branch-verification':'Branch_Geometry_Verification.json','/arrangement-record':'Graph_Arrangement_Control.json',
 '/arrangement-verification':'Graph_Arrangement_Verification.json',
 '/csv-response-record':'CSV_Only_Response_Study.json','/csv-response-features':'CSV_Only_Response_Features.csv',
 '/csv-response-parameters':'CSV_Only_Reference_Parameters.json','/csv-vector-groups':'CSV_Vector_Groups.csv',
 '/csv-response-verification':'CSV_Only_Verification.json','/paper.pdf':'Graph_Led_Stylometry_Manuscript.pdf',
 '/paper.md':'Graph_Led_Stylometry_Manuscript.md','/paper-references':'Paper_References.json',
 '/register':'Pattern_Register.json','/prototype-features':'M01_Prototype_Features.csv',
 '/prototype-parameters':'M01_Reference_Parameters.json','/cross-genre-record':'Cross_Genre_Review.json',
 '/recurring-record':'Recurring_Patterns.json','/recurring-features':'Recurring_Prototype_Features.csv',
 '/recurring-parameters':'Recurring_Reference_Parameters.json','/hyperbola-features':'R03_Hyperbola_Features.csv',
 '/expanded-record':'Expanded_Graph_Search.json','/microscope-record':'Graph_Microscope.json',
 '/control-record':'Graph_Control_Review.json','/measurement-audit':'Graph_Measurement_Audit.csv',
 '/verb-count-audit':'Verb_Count_Measurement_Audit.csv',
}
REPORT_ROUTES={
 '/branch-research':'Branch_Geometry_Study.md','/arrangement-research':'Graph_Arrangement_Control.md',
 '/reproduction':'REPRODUCE_RESEARCH.md','/csv-response-research':'CSV_Only_Response_Study.md',
 '/notebook':'Research_Notebook.md','/catalogue':'Pattern_Catalogue.md','/formula':'Formula_Design_Brief.md',
 '/formula-attempt':'M01_Formula_Attempt.md','/cross-genre-review':'Cross_Genre_Graph_Review.md',
 '/recurring-research':'Recurring_Patterns.md','/expanded-research':'Expanded_Graph_Search.md',
 '/microscope-research':'Graph_Microscope.md','/control-research':'Graph_Control_Review.md',
}
PAYLOAD_NAMES={
 'data':'original-tuples.json','candidates':'pattern-register.json','branch-study-data':'branch-study.json',
 'microscope-data':'microscope-context.json','expanded-search-data':'expanded-context.json',
}
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write_json(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def js_json(value):return json.dumps(value,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')

def main(research,owner,repository):
    research=research.resolve();out=PROJECT/'site';out.mkdir(exist_ok=True)
    manifest=json.loads((research/'Source_Manifest.json').read_text(encoding='utf-8'))
    assert manifest['active_pass']=='FIXED_CSV_GRAPH_LED_EXPLORATORY_RESEARCH_COMPLETE'
    atlas=research/'Graph_Interaction_Atlas.html';assert sha(atlas)==manifest['atlas_sha256']
    assert sha(research/'Research_System_Source.zip')==manifest['source_bundle_sha256']
    assert not (out/'downloads').exists() and not (out/'reports').exists(),'Preserve the complete preview privately before building the portal-only release'
    for path in ['assets/evidence','assets/js','assets/vendor','data']:(out/path).mkdir(parents=True,exist_ok=True)
    page=atlas.read_text(encoding='utf-8');scripts=list(re.finditer(r'<script([^>]*)>(.*?)</script>',page,re.S))
    assert len(scripts)==9
    payload_hashes={};image_hashes=set()
    def script_replacement(match):
        attributes,contents=match.groups()
        if 'type="application/json"' in attributes:
            identifier=re.search(r'id="([^"]+)"',attributes).group(1)
            filename=PAYLOAD_NAMES[identifier];target=out/'data'/filename;target.write_text(contents,encoding='utf-8')
            payload_hashes[identifier]=sha(target)
            return '<script id="'+identifier+'" type="application/json" data-src="data/'+filename+'"></script>'
        if contents.startswith('/**\n* plotly.js'):
            (out/'assets/vendor/plotly-3.7.0.min.js').write_text(contents,encoding='utf-8')
            return '<script src="assets/vendor/plotly-3.7.0.min.js" defer></script>'
        if contents.startswith("(()=>{'use strict';const d="):
            # Serialize render requests so rapid control changes cannot combine
            # one family's Human panel with another family's AI panel.
            previous="for(const id of ['branch-family','branch-genre','branch-metric'])el(id).addEventListener('change',()=>update().catch(e=>{el('branch-explanation').textContent='Plot rendering failed: '+e.message}));update().catch(e=>{el('branch-explanation').textContent='Plot rendering failed: '+e.message});})();"
            replacement="let drawing=false,pending=false;async function schedule(){if(drawing){pending=true;return}drawing=true;try{do{pending=false;await update()}while(pending)}catch(e){el('branch-explanation').textContent='Plot rendering failed: '+e.message}finally{drawing=false}}for(const id of ['branch-family','branch-genre','branch-metric'])el(id).addEventListener('change',schedule);schedule();})();"
            assert previous in contents;contents=contents.replace(previous,replacement)
            (out/'assets/js/branch-panel.js').write_text(contents,encoding='utf-8');return ''
        if 'function saveNote()' in contents:
            notes=(PROJECT/'tools/browser_notes.js').read_text(encoding='utf-8')
            contents,count=re.subn(r'function history\(state\)\{.*?\nasync function init\(\)\{',lambda _:notes+'\nasync function init(){',contents,count=1,flags=re.S);assert count==1
            old="try{apiState=await(await fetch('/api/state')).json();history(apiState)}catch(error){$('save-status').textContent='The viewer can draw offline, but saving requires the local workspace launcher.'}"
            new="try{apiState=loadBrowserNotes();history(apiState);$('export-notes').onclick=exportBrowserNotes}catch(error){$('save-status').textContent='Browser storage is unavailable: '+error.message+'. The graph explorer remains available.'}"
            assert old in contents;contents=contents.replace(old,new)
            assert "fetch('/api/" not in contents
            (out/'assets/js/atlas.js').write_text(contents,encoding='utf-8');return ''
        assert 'The viewer and Node checks use this same transformation code' in contents
        (out/'assets/js/view-math.js').write_text(contents,encoding='utf-8');return ''
    page=re.sub(r'<script([^>]*)>(.*?)</script>',script_replacement,page,flags=re.S)
    def image_replacement(match):
        content=base64.b64decode(match.group(1),validate=True);digest=hashlib.sha256(content).hexdigest()
        (out/'assets/evidence'/(digest+'.png')).write_bytes(content);image_hashes.add(digest)
        return 'assets/evidence/'+digest+'.png'
    page=re.sub(r'data:image/png;base64,([A-Za-z0-9+/=]+)',image_replacement,page)
    scientific_images=set(image_hashes)
    # The original 180-image inventory includes Plotly's embedded logo. Keep
    # its original vendor script intact and also preserve that PNG by hash.
    for vendor_image in re.finditer(r'data:image/png;base64,([A-Za-z0-9+/=]+)',scripts[0].group(2)):
        image_replacement(vendor_image)
    assert len(image_hashes)==180
    page=page.replace('<img ','<img loading="lazy" decoding="async" ')
    routes={'/manifest':'hosting-manifest.json','/results':'./#branch-study','/':'./'}
    private_routes=set(RESOURCE_ROUTES)|set(REPORT_ROUTES)|{'/source.zip'}
    def omit_private_link(match):
        return '' if urlsplit(match.group(2)).path in private_routes else match.group(0)
    page=re.sub(r'<a\b([^>]*?)href="(/[^\"]*)"([^>]*)>.*?</a>',omit_private_link,page,flags=re.S)
    page=re.sub(r'<div class="links">[\s·]*</div>','',page)
    def link_replacement(match):
        raw=match.group(1);parts=urlsplit(raw)
        assert parts.path in routes,'Unmapped local route: '+raw
        replacement=routes[parts.path]
        if parts.query:replacement+='?'+parts.query
        if parts.fragment:replacement+='#'+parts.fragment
        return 'href="'+html.escape(replacement,quote=True)+'"'
    page=re.sub(r'href="(/[^\"]*)"',link_replacement,page)
    page=page.replace('<html', '<html data-research-build="'+sha(research/'Source_Manifest.json')+'"',1)
    page=page.replace('<head>','<head><meta name="description" content="Explore collective stylometric feature interactions across Human and AI writing genres. Fixed-CSV graph-led exploratory research, formulas, controls and reproducible artifacts.">',1)
    page=page.replace('Save the observation with its exact feature set, scaling, document IDs and view settings. Notes are appended to your research journal.','Save a private browser note with its exact feature set, scaling, document IDs and view settings. Export your notes to retain a copy. The published research notebook remains unchanged.')
    page=page.replace('Save observation to research journal','Save observation in this browser')
    marker='<button id="save"';assert marker in page
    page=page.replace('<p id="save-status"','<button type="button" id="export-notes">Export my notes</button><p id="save-status"',1)
    # Existing tables need separate padding and wrapping at project-site widths.
    page=page.replace('</head>','<style>#branch-study th,#branch-study td{padding:7px 9px;text-align:left;vertical-align:top}#branch-study th{white-space:normal}#branch-study table{width:100%;border-collapse:collapse}#branch-study tr:nth-child(even){background:#f5f8fa}#portal-loading{padding:12px 20px;background:#edf6fa;color:#17333f}#export-notes{margin-left:8px}</style></head>',1)
    loading='<div id="portal-loading" role="status">Loading the fixed feature table and graph controls…</div><noscript>This portal needs JavaScript for interactive plots. The manuscript and downloadable research reports remain available through their links.</noscript>'
    page=page.replace('<body>', '<body>'+loading,1)
    public_notes=[]
    page=page.replace('</body>','<script id="published-notes" type="application/json">'+js_json(public_notes)+'</script><script src="assets/js/bootstrap.js" defer></script></body>',1)
    assert 'export-notes' in page and 'id="portal-loading"' in page
    (out/'index.html').write_text(page,encoding='utf-8');(out/'.nojekyll').write_text('',encoding='utf-8')
    shutil.copyfile(PROJECT/'tools/bootstrap.js',out/'assets/js/bootstrap.js')
    (out/'404.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Research portal</title><h1>Page not found</h1><p>Open the <a href="./">research portal</a> and use its links.</p></html>',encoding='utf-8')
    public={
      'schema_version':'exp03.github_pages_release.v1','built_at_utc':datetime.now(timezone.utc).isoformat(),
      'title':'Experiment 03 — Relational Graph Stylometry','author':'Muhammad Ismail',
      'research_status':manifest['active_pass'],'research_build_sha256':sha(research/'Source_Manifest.json'),
      'source_csv_sha256':manifest['data_sha256'],'rows':5046,'features':132,
      'research_data':'Fixed feature CSV and derived graphs only','publication_scope':'EXPLORATORY_FIXED_CSV_STUDY',
      'public_scope':'INTERACTIVE_PORTAL_ONLY_NO_RESEARCH_DOWNLOADS',
      'research_refitted_for_hosting':False,'graph_png_assets':len(scientific_images),'png_assets':180,
      'interactive_payload_sha256':payload_hashes,'original_graph_sha256':sorted(image_hashes),
      'download_sha256':{},'repository':f'{owner}/{repository}',
      'notes_storage':'Private browser localStorage with visitor note export; research notebook remains local',
      'route_map':routes,
    }
    write_json(out/'hosting-manifest.json',public)
    report={'static_portal':'BUILT','files':sum(p.is_file() for p in out.rglob('*')),'bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'index_bytes':(out/'index.html').stat().st_size,'graph_assets':len(scientific_images),'all_png_assets':180,'research_refitted':False,'repository':public['repository']}
    (PROJECT/'verification').mkdir(exist_ok=True);write_json(PROJECT/'verification/Build_Record.json',report);print(json.dumps(report))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--research-root',type=Path,required=True);parser.add_argument('--owner',required=True);parser.add_argument('--repository',default='relational-graph-stylometry');args=parser.parse_args();main(args.research_root,args.owner,args.repository)
