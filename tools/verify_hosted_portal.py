"""Verify the deployed or prefixed preview files against the checked site."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from concurrent.futures import ThreadPoolExecutor
import argparse,hashlib,json
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
def main(base_url,release,paths=None):
    base_url=base_url.rstrip('/')+'/'
    expected=json.loads((ROOT/'site/hosting-manifest.json').read_text(encoding='utf-8'))
    checks=0
    def verify(path):
        relative=path.relative_to(ROOT/'site').as_posix()
        with urlopen(Request(base_url+relative,headers={'User-Agent':'Relational-Graph-Stylometry-Verification'}),timeout=90) as response:
            digest=hashlib.file_digest(response,'sha256').hexdigest()
            assert response.status==200,relative
        with path.open('rb') as stream:assert digest==hashlib.file_digest(stream,'sha256').hexdigest(),relative
        return 1
    files=[p for p in sorted((ROOT/'site').rglob('*')) if p.is_file() and p.name!='.nojekyll']
    if paths:
        available={p.relative_to(ROOT/'site').as_posix():p for p in files}
        assert set(paths)<=set(available)
        files=[available[name] for name in paths]
    with ThreadPoolExecutor(max_workers=6) as pool:checks=sum(pool.map(verify,files))
    unavailable=['downloads/Graph_Led_Stylometry_Manuscript.pdf','downloads/Branch_Synthetic_Features.csv','downloads/Branch_Geometry_Parameters.zip','Research_System_Source.zip','reports/notebook.html','AIJ_Manuscript.pdf','AIJ_Manuscript.docx','AIJ_Submission_Package.zip','downloads/AIJ_Manuscript.pdf','downloads/AIJ_Manuscript.docx']
    for relative in unavailable:
        try:urlopen(base_url+relative,timeout=30)
        except HTTPError as error:assert error.code==404,relative
        else:raise AssertionError('An excluded research artifact is available: '+relative)
    if release:
        with urlopen(expected['source_bundle_url'],timeout=120) as response:
            assert hashlib.file_digest(response,'sha256').hexdigest()==expected['source_bundle_sha256']
    record={'status':'PASS','checked_at_utc':datetime.now(timezone.utc).isoformat(),'base_url':base_url,'files_verified_byte_for_byte':checks,'paths':paths,'source_release_verified':release,'excluded_research_paths_checked_404':len(unavailable),'source_csv_sha256':expected['source_csv_sha256'],'research_build_sha256':expected['research_build_sha256']}
    filename='Hosted_Final_Changes_Verification.json' if paths else 'Hosted_Verification.json'
    target=ROOT/'verification'/(filename if base_url.startswith('https://') else 'Preview_HTTP_Verification.json')
    target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base-url',required=True);parser.add_argument('--release',action='store_true');parser.add_argument('--paths',nargs='+');args=parser.parse_args();main(args.base_url,args.release,args.paths)
