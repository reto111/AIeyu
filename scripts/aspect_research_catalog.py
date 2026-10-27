"""Verify the explicit local research catalog, without opening student data."""
import argparse,hashlib,json
from pathlib import Path
DEFAULT=Path(__file__).resolve().parents[1]/'data/processed/aspect_reference/research_catalog_20261024_001.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def local(root,relative):
    path=(root/relative).resolve()
    if not path.is_relative_to(root.resolve()):raise ValueError('Catalog path escapes research directory')
    return path
def verify(path):
    path=path.resolve();root=path.parent;catalog=json.loads(path.read_text('utf8'));count=0;packages=[]
    for item in catalog['packages']:
        manifest=local(root,item['manifest'])
        if sha(manifest)!=item['manifest_sha256']:raise ValueError('Catalog manifest mismatch: '+item['key'])
        data=json.loads(manifest.read_text('utf8'));package=manifest.parent
        for relative,h in data['files'].items():
            target=local(package,relative)
            if sha(target)!=h:raise ValueError('Package changed: '+item['key']+'/'+relative)
            count+=1
        packages.append(dict(key=item['key'],files=len(data['files'])))
    for item in catalog['evidence_reports']:
        if sha(local(root,item['path']))!=item['sha256']:raise ValueError('Evidence report changed')
    return dict(verified=True,packages=packages,package_files_verified=count,evidence_reports_verified=len(catalog['evidence_reports']),external_calls=0,student_database_opened=False,semantic_correctness_certified=False)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['list','verify']);p.add_argument('--catalog',type=Path,default=DEFAULT);a=p.parse_args()
    if a.command=='verify':print(json.dumps(verify(a.catalog),ensure_ascii=False,indent=2))
    else:
        data=json.loads(a.catalog.read_text('utf8'));print(json.dumps([dict(key=x['key'],manifest=x['manifest'],purpose_zh=x['purpose_zh'])for x in data['packages']],ensure_ascii=False,indent=2))
