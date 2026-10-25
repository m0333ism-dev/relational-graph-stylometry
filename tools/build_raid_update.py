"""Publish numerical graph views and frozen summaries, excluding research downloads."""
from pathlib import Path
from datetime import datetime, timezone
from copy import deepcopy
import argparse
import csv
import hashlib
import html as html_module
import json
import math
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT/'site'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)+'\n', encoding='utf-8', newline='\n')

def main(explorer, atlas_root, atlas_index, frozen, summary):
    source = json.loads((explorer/'data.json').read_text(encoding='utf-8'))
    results = json.loads((frozen/'Final_Results.json').read_text(encoding='utf-8'))
    assert sha(frozen/'Final_Results.json') == '7eb7c89e9b38c2672d483e295920c6a8ad9412d7ed395073b57ff2577720074c'
    assert sha(frozen/'Final_features_132.csv') == 'c7b1c1478f4cb0aab6cde7088f0549559694ddf6077690a00f8e486fd451e76b'
    assert source['final_evaluation']['primary_macros'] == results['primary_macros']
    assert source['secondary_controls']['parameters_sha256'] == 'a6c80a03b37e57dfca51d22e4803917ef7e1a12d4c2a3a235ce801fb23ac1703'
    assert len(source['names']) == 132 and len(source['domains']) == 8
    raid = SITE/'raid'; raid.mkdir(exist_ok=True)
    cohort_counts = {'discovery':1600, 'structural':2398, 'final':2390}
    metadata = {k: deepcopy(source[k]) for k in ['names','domains','groups','candidates','scales','audit','confirmation','final_evaluation','secondary_controls','default_cohort','default_candidate']}
    metadata['secondary_controls'] = {k: metadata['secondary_controls'][k] for k in ['stage','parameters_sha256','macro_scores','joint_minus_frozen_comparator','scope']}
    metadata['confirmation'] = {k: metadata['confirmation'][k] for k in ['included_pairs','excluded_pairs','primary_macros','scope']}
    metadata['schema'] = 'exp03.raid.public_numeric_explorer.v1'
    metadata['public_scope'] = 'INTERACTIVE_NUMERICAL_GRAPHS_NO_GENERATION_PROSE_OR_RESEARCH_DOWNLOADS'
    metadata['cohorts'] = {}
    numeric_hashes = {}
    for key, expected in cohort_counts.items():
        cohort = source['cohorts'][key]
        assert len(cohort['rows']) == expected
        rows = deepcopy(cohort['rows'])
        for row in rows:
            assert set(row) <= {'id','source_id','domain','label','v','u','synthetic','reference_scores'}
            assert len(row['v']) == len(row['u']) == 132
            assert all(math.isfinite(v) for v in row['v']+row['u'])
            assert row['domain'] in source['domains'] and row['label'] in ['human','ai']
        path = raid/'data'/(key+'.json'); dump(path, rows)
        name = cohort['name']
        if key == 'structural': name = 'Structural check, then formula development: 1,199 source pairs'
        metadata['cohorts'][key] = {'name':name, 'rows_count':expected, 'path':'data/'+key+'.json'}
        numeric_hashes[key] = sha(path)
    metadata['candidates'].insert(2, {
        'id':'S01','name':'Local adverb and advmod band width',
        'members':['adverb_ratio','dep_advmod_ratio','avg_sent_length'],
        'context_to_inspect':[], 'default_colour':'', 'default_size':'', 'default_projection':'xy',
        'graph_prompt':'Inspect the adverb/advmod band and its local spread. Sentence length is optional 3D context; the frozen S01 endpoint uses the two modifier-band features. See the fixed-curve all-genre atlas below.',
        'status_text':'Positive average local width contrast; all eight point estimates positive, with uncertain poetry/reddit effects. A necessary third member is not claimed'
    })
    dump(raid/'metadata.json', metadata)
    source_html = (explorer/'index.html').read_text(encoding='utf-8')
    javascript = source_html.split("<script>\n'use strict';",1)[1].split('</script>',1)[0]
    page = source_html.split("<script>\n'use strict';",1)[0]+'<script src="explorer.js" defer></script></body></html>\n'
    page = page.replace('<title>RAID graph-led interaction research</title>', '<title>RAID recurring interaction patterns across genres</title>')
    page = page.replace('<script src="plotly.min.js"></script>', '<script src="../assets/vendor/plotly-3.7.0.min.js"></script>')
    page = page.replace('<h1>RAID graph-led interaction research</h1>',
        '<nav aria-label="Research studies"><a href="../">Original-corpus explorer</a> · <a href="#finalSummary">Frozen results</a> · <a href="#complete-atlas">All-genre atlas</a></nav><h1>Recurring interaction patterns across eight genres</h1>')
    page = page.replace('The target is a collective interaction pattern: band shape, branches, convergence, divergence or how another member varies along their configuration. Compare discovery, structural development and the completed frozen final evaluation below.',
        'The empirical contribution is the identification and mathematical characterization of recurring Human-AI feature relationships. Bands, collective following and local spread are the research objects. The formulas and analysis system support their description. Compare discovery, structural development and the frozen final evaluation; these have different evidence roles.')
    page = re.sub(r'<p><a href="\.\./pattern_geometry/final_validation_01/Final_Research_Readout\.md".*?</p>', '', page, count=1, flags=re.S)
    page = re.sub(r'<p><a href="\.\./pattern_geometry/confirmation_01/Structural_Findings\.md".*?</p>', '', page, count=1, flags=re.S)
    page = page.replace('Loading the numerical feature CSV view…', 'Loading the numerical graph values…')
    page = page.replace('<label>Research cohort<select id="cohort">', '<label>Evidence stage<select id="cohort">')
    page = page.replace('<h2>Choose a joint configuration</h2>', '<h2>Choose a joint configuration</h2><p class="muted">C04, B06 and S01 are linked to the stated frozen components. The other starting configurations are exploratory nominations, not additional confirmed findings.</p>')
    images = []
    atlas = json.loads(atlas_index.read_text(encoding='utf-8'))
    for item in atlas:
        n = item['number']; filename = f'Supplement_{n:02d}_{item["family"]}.png'
        # The presentation manifest supplies the actual immutable image path.
        matches = [atlas_root/f'Supp_{item["family"]}_{((n-1)%4)+1:02d}.png']
        matches = [p for p in matches if p.is_file()]
        assert len(matches) == 1, (n, [p.name for p in matches])
        target = raid/'figures'/filename; target.parent.mkdir(exist_ok=True); shutil.copy2(matches[0], target)
        assert sha(target) == sha(matches[0])
        images.append({'number':n,'family':item['family'],'genres':item['genres'],'path':'figures/'+filename,'sha256':sha(target),'caption':item['caption']})
    assert summary.exists()
    shutil.copy2(summary,raid/'figures/Frozen_Components.png')
    atlas_parts = ['<section class="card" id="complete-atlas"><h2>Complete final all-genre atlas</h2><p>These are the recorded final tuples, not fitted reconstructions. Every eligible document is retained: 150 per class and genre except poetry with 145. Common ranges and discovery-fitted transforms are unchanged. Recurring components have the stated exceptions; the clouds are not identical across genres.</p>']
    for family,title in [('C04','Sentence centre and spread'),('B06','Clause band and dependency depth'),('S01','Local modifier-band width')]:
        atlas_parts.append(f'<details id="{("modifier-band-atlas" if family=="S01" else "atlas-"+family.lower())}"><summary>{family} · {title} · all eight genres</summary>')
        for image in images:
            if image['family'] != family: continue
            atlas_parts.append('<figure><img loading="lazy" decoding="async" style="width:100%;height:auto" alt="'+html_module.escape(family+' in '+' and '.join(image['genres']))+'" src="'+image['path']+'"><figcaption>'+html_module.escape(image['caption'])+'</figcaption></figure>')
        atlas_parts.append('</details>')
    atlas_parts += ['<details><summary>Four frozen components and genre uncertainty</summary><figure><img loading="lazy" decoding="async" style="width:100%;height:auto" src="figures/Frozen_Components.png" alt="Genre estimates and intervals for all four frozen components"><figcaption>Genre intervals are unadjusted; equal-genre average intervals adjust across the four primary endpoints. Effects have different units. The observations and intervals are unchanged.</figcaption></figure></details>',
        '<p><strong>Scope.</strong> New source groups come from genres already seen in development, within one recorded historical ChatGPT configuration. The exact model version is unavailable. These data support the specified components, with reversals and uncertainty; they establish neither universal invariance, complete conditional geometry nor a calibrated detector.</p>',
        '<details><summary>Feature definitions and discovery-cohort audit</summary><p>Constants, aliases and proportional measurements remain available for inspection and do not constitute new interactions. Class/genre midranks are a separate dependence diagnostic, not preprocessing for class-unknown predictions. The stop_word_ratio feature uses the custom FUNCTION_WORDS list, while run-length features use spaCy STOP words; their lexicons differ.</p><pre id="audit"></pre></details>',
        '<p>Related research: <a href="https://aclanthology.org/2024.acl-long.674/">RAID benchmark</a> · <a href="https://arxiv.org/abs/2608.27855v2">Consistent stylometric footprints</a> · <a href="https://aclanthology.org/2024.naacl-long.95/">Ghostbuster feature combinations</a>.</p>',
        '<p class="muted">This public explorer serves numerical measurements and document/source IDs required for the plots. Manuscripts, notebooks, CSV exports and research archives are not hosted here. The complete tuples and summaries are unchanged by publication.</p></section>']
    page,n = re.subn(r'<section class="card"><h2>Research record and evidence</h2>.*?</section>',lambda _:''.join(atlas_parts),page,count=1,flags=re.S)
    assert n == 1 and '../pattern_geometry/' not in page and '.md"' not in page
    page = page.replace('table{border-collapse', 'figure{margin:16px 0}figcaption{font-size:13px;color:#4b5c69}nav{margin-bottom:14px;font-size:14px}summary{cursor:pointer;font-weight:600}#audit{white-space:pre-wrap;overflow-wrap:anywhere}table{border-collapse')
    javascript = "'use strict';"+javascript
    refresh = '''const cohortCache=new Map();let cohortLoad=0;
async function getCohortRows(key){if(cohortCache.has(key))return cohortCache.get(key);const response=await fetch(D.cohorts[key].path);if(!response.ok)throw new Error('Cohort values unavailable');const rows=await response.json();if(rows.length!==D.cohorts[key].rows_count)throw new Error('Unexpected cohort row count');cohortCache.set(key,rows);return rows;}
function updateURL(){const q=new URLSearchParams({cohort:$('cohort').value,candidate:$('candidate').value,genre:$('domain').value,scale:$('scale').value});history.replaceState(null,'','?'+q+location.hash);}
function updateFooter(){$('footer').textContent=D.cohorts[$('cohort').value].name+' · '+D.rows.length.toLocaleString()+' complete numerical rows · '+D.names.length+' measured features · '+D.domains.length+' genres. Formulas and evaluation are unchanged.';}
async function refreshCohort(){const key=$('cohort').value,load=++cohortLoad;$('loading').hidden=false;$('loading').textContent='Loading '+D.cohorts[key].name+'…';document.querySelectorAll('select,button').forEach(el=>el.disabled=true);try{const rows=await getCohortRows(key);if(load!==cohortLoad)return;D.rows=rows;selection=null;$('selection').textContent='No point selected.';updateFooter();updateURL();draw();$('loading').hidden=true;}catch(error){$('loading').textContent='Cannot load the graph values: '+error.message;}finally{if(load===cohortLoad)document.querySelectorAll('select,button').forEach(el=>el.disabled=false);}}
'''
    javascript,n = re.subn(r'function refreshCohort\(\).*?(?=function structuralSummary\()',lambda _:refresh,javascript,count=1,flags=re.S)
    assert n == 1
    # Retain the existing graph and summary calculations; only source loading changes.
    javascript = javascript.replace("fetch('data.json').then", "fetch('metadata.json').then",1)
    javascript = javascript.replace('.then(data=>{D=data;', '.then(async data=>{D=data;',1)
    javascript = javascript.replace("$('cohort').onchange=refreshCohort;", "$('cohort').onchange=refreshCohort;",1)
    javascript = javascript.replace("$('candidate').onchange=chooseCandidate;", "$('candidate').onchange=()=>{chooseCandidate();updateURL();};",1)
    javascript = javascript.replace("'No point selected.';draw();});", "'No point selected.';draw();updateURL();});",1)
    ending = "$('cohort').value=D.default_cohort||'discovery';D.rows=D.cohorts[$('cohort').value].rows;$('candidate').value=D.default_candidate||D.candidates[0].id;$('scale').value='asinh';chooseCandidate();refreshCohort();"
    replacement = "const q=new URLSearchParams(location.search);$('cohort').value=D.cohorts[q.get('cohort')]?q.get('cohort'):D.default_cohort||'final';$('domain').value=D.domains.includes(q.get('genre'))?q.get('genre'):D.domains[0];D.rows=await getCohortRows($('cohort').value);$('candidate').value=D.candidates.some(c=>c.id===q.get('candidate'))?q.get('candidate'):D.default_candidate||D.candidates[0].id;$('scale').value=['raw','minmax','asinh','rank'].includes(q.get('scale'))?q.get('scale'):'asinh';chooseCandidate();updateFooter();updateURL();$('loading').hidden=true;"
    assert ending in javascript
    javascript = javascript.replace(ending,replacement,1)
    javascript = javascript.replace("$('loading').hidden=true;$('structuralSummary')", "$('structuralSummary')",1)
    (raid/'index.html').write_text(page,encoding='utf-8',newline='\n')
    (raid/'explorer.js').write_text(javascript,encoding='utf-8',newline='\n')

    # Keep every pre-existing original-corpus payload and graph unchanged.
    index = SITE/'index.html'
    original = index.read_text(encoding='utf-8')
    updated = original.replace('<title>Experiment 03 · Feature interaction atlas</title>', '<title>Recurring feature interaction patterns in human and AI writing</title>')
    updated = updated.replace('Explore collective stylometric feature interactions across Human and AI writing genres. Fixed-CSV graph-led exploratory research, formulas, controls and reproducible artifacts.', 'Explore recurring Human and AI feature configurations across genres, with original-corpus graphs, RAID numerical views, frozen results and documented exceptions.')
    updated = updated.replace('<h1>Feature interaction atlas</h1>', '<h1>Recurring feature interaction patterns</h1>')
    updated = updated.replace('Find recurring collective interactions across genres. Describe their geometry. Craft formulas to capture it.', 'Discover how linguistic features jointly organize across genres in Human and AI writing. Characterize the recurring relationships, their uncertainty and their exceptions.')
    updated = updated.replace('<a class="header-link" href="#capture-study">Latest graph comparisons</a>', '<a class="header-link" href="raid/">RAID interaction explorer</a> <a class="header-link" href="#capture-study">Original-corpus reconstructions</a>')
    overview = '''<section class="record" id="research-findings"><h2>Empirical discoveries across genres</h2><p>The primary contribution is the identification and mathematical characterization of specified recurring feature-interaction patterns. Two members can form a band while another follows their collective progression or has a different local spread. Recurrence concerns the measured relationship; it does not require identical feature values or an unchanged cloud in every genre. Formulas and the analysis system support the discoveries.</p><div class="catalogue-grid"><article class="motif"><h3>Original-corpus study</h3><p>5,046 documents and 132 features. Sentence-envelope and modifier/depth configurations have recurring components with genre exceptions. The analysis is exploratory; reconstruction remains partial.</p><a href="#capture-study">Inspect the original configurations and their reconstructions</a></article><article class="motif"><h3>RAID study and frozen evaluation</h3><p>One recorded ChatGPT configuration across eight genres. A final evaluation on 1,195 new source pairs supports four specified average components, retaining genre reversals and uncertainty. All eight genres appeared in development.</p><a href="raid/">Explore the RAID tuples, all-genre atlas and frozen results</a></article></div><p class="hint">The studies have separate discovery histories. The RAID evaluation does not independently validate the original formulas. Neither study establishes universal genre invariance or a deployable detector.</p></section>'''
    if 'id="research-findings"' not in updated: updated = updated.replace('<div class="content">','<div class="content">\n'+overview,1)
    assert updated != original or 'id="research-findings"' in original
    index.write_text(updated,encoding='utf-8',newline='\n')
    manifest_path = SITE/'hosting-manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['updated_at_utc'] = datetime.now(timezone.utc).isoformat()
    manifest['title'] = 'Recurring feature interaction patterns across genres in human and AI writing'
    manifest['publication_scope'] = 'ORIGINAL_EXPLORATORY_AND_RAID_WITHIN_CONFIGURATION_FROZEN_COMPONENTS'
    manifest['research_status'] = 'QUALIFIED_RECURRING_COMPONENTS_WITH_GENRE_EXCEPTIONS'
    manifest['raid'] = {
        'path':'raid/','features':132,'genres':8,'cohort_rows':cohort_counts,
        'final_source_pairs':1195,'final_features_sha256':sha(frozen/'Final_features_132.csv'),
        'final_results_sha256':sha(frozen/'Final_Results.json'),
        'parameters_sha256':source['secondary_controls']['parameters_sha256'],
        'cohort_numeric_payload_sha256':numeric_hashes,
        'files_sha256':{p.relative_to(raid).as_posix():sha(p) for p in sorted(raid.rglob('*')) if p.is_file()},
        'all_genre_atlas':images,'new_fits':False,'new_inference':False,
        'generation_prose_included':False,'research_downloads':False}
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    verification = ROOT/'verification';verification.mkdir(exist_ok=True)
    record={'status':'BUILT','built_at_utc':datetime.now(timezone.utc).isoformat(),
            'source_explorer_json_sha256':sha(explorer/'data.json'),
            'source_explorer_html_sha256':sha(explorer/'index.html'),
            'source_final_results_sha256':sha(frozen/'Final_Results.json'),
            'cohort_rows':cohort_counts,'features':132,'genres':8,'all_genre_atlas_images':12,
            'numeric_rows_preserved_exactly':True,'metadata_split_for_lazy_loading':True,
            'private_research_links_removed':True,'manuscript_included':False,'new_fits':False}
    (verification/'RAID_Build_20261025.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--explorer-root',type=Path,required=True)
    p.add_argument('--atlas-root',type=Path,required=True)
    p.add_argument('--atlas-index',type=Path,required=True)
    p.add_argument('--frozen-root',type=Path,required=True)
    p.add_argument('--summary-figure',type=Path,required=True)
    a=p.parse_args();main(a.explorer_root,a.atlas_root,a.atlas_index,a.frozen_root,a.summary_figure)
