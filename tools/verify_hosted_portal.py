"""Verify the deployed or prefixed preview files against the checked site."""
from pathlib import Path
from urllib.request import Request,urlopen
import argparse,hashlib,json
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
def main(base_url,release):
    base_url=base_url.rstrip('/')+'/'
    expected=json.loads((ROOT/'site/hosting-manifest.json').read_text(encoding='utf-8'))
    checks=0
    for path in sorted((ROOT/'site').rglob('*')):
        if not path.is_file() or path.name=='.nojekyll':continue
        relative=path.relative_to(ROOT/'site').as_posix()
        with urlopen(Request(base_url+relative,headers={'User-Agent':'Relational-Graph-Stylometry-Verification'}),timeout=90) as response:
            digest=hashlib.file_digest(response,'sha256').hexdigest()
            assert response.status==200,relative
        with path.open('rb') as stream:assert digest==hashlib.file_digest(stream,'sha256').hexdigest(),relative
        checks+=1
    if release:
        with urlopen(expected['source_bundle_url'],timeout=120) as response:
            assert hashlib.file_digest(response,'sha256').hexdigest()==expected['source_bundle_sha256']
    record={'status':'PASS','checked_at_utc':datetime.now(timezone.utc).isoformat(),'base_url':base_url,'files_verified_byte_for_byte':checks,'source_release_verified':release,'source_csv_sha256':expected['source_csv_sha256'],'research_build_sha256':expected['research_build_sha256']}
    target=ROOT/'verification'/('Hosted_Verification.json' if release else 'Preview_HTTP_Verification.json')
    target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base-url',required=True);parser.add_argument('--release',action='store_true');args=parser.parse_args();main(args.base_url,args.release)
