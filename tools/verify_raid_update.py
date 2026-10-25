"""Verify public graph values against saved cohorts and frozen numerical evidence."""
from pathlib import Path
from html.parser import HTMLParser
from collections import Counter
from datetime import datetime, timezone
import argparse,csv,hashlib,json,re

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main(explorer,frozen):
    site=ROOT/'site';raid=site/'raid'
    source=json.loads((explorer/'data.json').read_text(encoding='utf-8'))
    meta=json.loads((raid/'metadata.json').read_text(encoding='utf-8'))
    manifest=json.loads((site/'hosting-manifest.json').read_text(encoding='utf-8'))
    assert manifest['public_scope']=='INTERACTIVE_PORTAL_ONLY_NO_RESEARCH_DOWNLOADS'
    for key in ['names','domains','groups','scales','audit','final_evaluation']:
        assert meta[key]==source[key],key
    counts={};all_rows={}
    for key,n in [('discovery',1600),('structural',2398),('final',2390)]:
        rows=json.loads((raid/meta['cohorts'][key]['path']).read_text(encoding='utf-8'))
        assert rows==source['cohorts'][key]['rows'],key
        assert len(rows)==meta['cohorts'][key]['rows_count']==n
        assert len(set(r['id'] for r in rows))==n
        assert set(Counter(r['source_id'] for r in rows).values())=={2}
        assert all(len(r['v'])==len(r['u'])==132 for r in rows)
        counts[key]=n;all_rows[key]=rows
    audit=json.loads((frozen/'Final_Cohort_Audit.json').read_text(encoding='utf-8'))
    excluded=set(audit['excluded_source_groups'])
    assert len(excluded)==5 and audit['exclusion_rule_frozen_before_extraction'] is True
    with (frozen/'Final_features_132.csv').open(encoding='utf-8-sig',newline='') as f:
        extracted=list(csv.DictReader(f))
    assert len(extracted)==2400
    expected={r['id']:r for r in extracted if r['source_id'] not in excluded}
    assert set(expected)=={r['id'] for r in all_rows['final']}
    for row in all_rows['final']:
        old=expected[row['id']]
        assert [float(old[name]) for name in meta['names']]==row['v'],row['id']
        assert old['source_id']==row['source_id'] and old['domain']==row['domain']
        assert old['label'].lower()==row['label']
    genre_counts=Counter((r['domain'],r['label']) for r in all_rows['final'])
    assert all(n==(145 if genre=='poetry' else 150) for (genre,label),n in genre_counts.items())
    results=json.loads((frozen/'Final_Results.json').read_text(encoding='utf-8'))
    assert meta['final_evaluation']['primary_macros']==results['primary_macros']
    assert meta['secondary_controls']['macro_scores']==source['secondary_controls']['macro_scores']
    assert meta['secondary_controls']['parameters_sha256']==sha(frozen/'Final_Parameters.json')
    for name,digest in manifest['raid']['files_sha256'].items():assert sha(raid/name)==digest,name
    assert len(manifest['raid']['all_genre_atlas'])==12
    for family in ['C04','B06','S01']:
        items=[x for x in manifest['raid']['all_genre_atlas'] if x['family']==family]
        assert len(items)==4 and sorted(g for x in items for g in x['genres'])==sorted(meta['domains'])
    for p in site.rglob('*'):
        if p.is_file():assert p.suffix.lower() not in ['.pdf','.docx','.csv','.zip','.md','.jsonl'],p
    text=(raid/'index.html').read_text(encoding='utf-8')
    assert '../pattern_geometry/' not in text and 'Private research workbench' not in text
    assert 'Final_Research_Readout' not in text and 'RAID_Manuscript_Insert' not in text
    assert 'private local workbench' not in text and 'loading="lazy"' in text
    assert 'class-unknown' in text and 'already seen in development' in text
    js=(raid/'explorer.js').read_text(encoding='utf-8')
    assert "fetch('metadata.json')" in js and 'getCohortRows' in js and 'updateURL' in js
    assert 'not a class-blind predictor' in js
    assert 'research-findings' in (site/'index.html').read_text(encoding='utf-8')
    assert not re.search(r'[A-Z]:[\\/]|C:/Users|D:/Masters',text+js)
    record={'status':'PASS','checked_at_utc':datetime.now(timezone.utc).isoformat(),
            'cohort_rows_verified_exactly':counts,'features':132,'genres':8,
            'final_csv_numeric_values_checked':2390*132,
            'final_source_pairs':1195,'frozen_whole_source_exclusions_preserved':5,
            'primary_estimates_and_intervals_unchanged':True,
            'secondary_comparator_values_unchanged':True,'shared_scales_and_ranks_unchanged':True,
            'all_genre_atlas_images_verified':12,'public_research_downloads':0,
            'generation_prose_included':False,'new_fits':False,'new_inference':False}
    (ROOT/'verification/RAID_Verification_20261025.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--explorer-root',type=Path,required=True);p.add_argument('--frozen-root',type=Path,required=True)
    a=p.parse_args();main(a.explorer_root,a.frozen_root)
