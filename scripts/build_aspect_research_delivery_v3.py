"""Package only explicitly catalogued textbook research files, deterministically."""
import argparse,json,shutil,zipfile
from pathlib import Path
from aspect_research_catalog import verify,sha,local
from build_aspect_example_index import write

def build(catalog,output):
    if output.exists()or output.with_suffix('.zip').exists():raise FileExistsError('Immutable delivery')
    verification=verify(catalog);data=json.loads(catalog.read_text('utf8'));base=catalog.resolve().parent;output.mkdir(parents=True)
    members={catalog.resolve():Path(catalog.name),Path(__file__).with_name('aspect_research_catalog.py'):Path('aspect_research_catalog.py'),Path(__file__).with_name('aspect_corpus_search.py'):Path('aspect_corpus_search.py'),Path(__file__).with_name('aspect_corpus_language_lookup.py'):Path('aspect_corpus_language_lookup.py')}
    package_paths={item['key']:Path(item['manifest']).parent for item in data['packages']}
    def stats(key):return json.loads(local(base,package_paths[key].as_posix()+'/manifest.json').read_text('utf8'))['statistics']
    inline=stats('unnumbered_supplement');parallel=stats('unnumbered_parallel_supplement');roles=stats('reviewed_material_roles')
    for item in data['packages']:
        manifest=local(base,item['manifest']);m=json.loads(manifest.read_text('utf8'));members[manifest]=manifest.relative_to(base)
        for relative in m['files']:
            p=local(manifest.parent,relative);members[p]=p.relative_to(base)
    for item in data['evidence_reports']:
        p=local(base,item['path']);members[p]=p.relative_to(base)
    for source,relative in sorted(members.items(),key=lambda x:x[1].as_posix()):
        if relative.name in {'.env','russian_ai_tutor.sqlite'}:raise ValueError('Private data prohibited')
        target=output/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    lines=[f'# 现代俄语体学：{output.name}','',f"目录包含{len(data['packages'])}个研究包、{verification['package_files_verified']}个包内文件与{len(data['evidence_reports'])}份证据报告。无原PDF、外证档案原件、学生数据、密钥或外部API配置。",'',
    '理论层为40原ready、53模型编校候选、7隔离；默认只读原ready。编号044保留1453完整教材例组，默认269/显式候选1336，117隔离不返回；这与首段索引1453锚点是不同计量口径。', '',
    f"无编号补充{inline['records']}例组，默认{inline['eligible_original']}/显式{inline['eligible_with_candidates']}；现有俄汉对应{parallel['pairs']}组，覆盖{parallel['examples_with_pairs']}例组。另{parallel['russian_only_examples']}个圈定片段仅收俄文，不表示原书无汉译；另{parallel.get('chinese_only_examples',0)}个片段仅收汉语，不补译。例组、译对、10表194格分别计量，不相加当自然语料句数。", '',
    f"材料角色收{roles['paragraphs']}段、{roles['units']}理论单元，默认316/显式1216、117隔离。角色关联{roles['linked_illustration_groups']}例/10表；未链接不表示无例，全量角色阅读不表示行内例穷尽。星号、问号、斜线替换与括号改写保留。", '',
    '100学习卡350主张、22目标多轴试标均为同一助手材料；独立复核空包003有264空格，实际独立标注0。7来源疑点保持隔离。工程验收不能证明语言学正确率、翻译金标、专家一致率或自然语料代表性。', '',
    '## 包目录','']
    numbered=stats('numbered_parallel_language');mono=stats('numbered_monolingual_language')
    lines[2:2]=[f"新增编号语言层：{numbered['reviewed_groups']}双语组/{numbered['component_correspondences']}组成部分对应，加{mono['reviewed_groups']}单语组（29汉/3俄）。全部1336可用编号组完成范围审核，117隔离不返回。语言层按来源ID挂接，例组总数仍{1453+inline['records']}、默认{269+inline['eligible_original']}、显式{1336+inline['eligible_with_candidates']}；旧22目标重合不另加。不是译文金标、逐句对齐或自然语料。",'',f'新统一入口：`python -X utf8 aspect_corpus_language_lookup.py stats`；候选加`--include-candidates`。`show --id 来源ID --include-candidates`同时显示原转录、编校候选和编号语言对应。`search --term 文字`仍搜整组，含署名、译文和比较材料，不能据此算词频。旧统一入口须显式传本目录{catalog.name}。','']
    for item in data['packages']:lines.append(f"- [{item['key']}]({Path(item['manifest']).parent.as_posix()}/README.md)：{item['purpose_zh']}。")
    lines += ['', '## 离线运行','', '只需Python标准库，在解压目录执行：','', '```powershell',f'python -X utf8 aspect_research_catalog.py verify --catalog {catalog.name}',
    'python -X utf8 research_exports/aspect_editorial_candidate_20261023_002/aspect_candidate_rag.py prepare "未完成体为什么能表示已经达到结果？" --include-candidates',
    f"python -X utf8 {package_paths['unnumbered_supplement'].as_posix()}/aspect_unnumbered_examples.py list --include-candidates",
    f"python -X utf8 {package_paths['reviewed_material_roles'].as_posix()}/aspect_material_roles.py search --text 结果存在 --include-candidates",
    f'python -X utf8 aspect_corpus_search.py stats --catalog {catalog.name} --include-candidates',
    f'python -X utf8 aspect_corpus_search.py search --catalog {catalog.name} --term писал --match cyrillic_form --include-candidates',
    f'python -X utf8 aspect_corpus_search.py show --catalog {catalog.name} --id aspect.ch10.s02.03.example.047.01 --include-candidates','```','',
    'source_text是归档转录，candidate_text重放既有编校；context和材料段包含作者分析，不可冒充纯例文本。引用应保留版本、原页及状态。完整归档含隔离材料，禁止整目录默认导入检索或练习池。包内历史构建脚本仅供追溯；完整重建仍需原项目输入，离线运行承诺仅指现成包的只读入口。','',
    '本包按所附目录固定材料入口，所有旧目录与旧ZIP保持冻结。旧证据报告按原日期和覆盖范围解释，不冒充新增范围验收。统一查询须显式传所附目录；默认查询原ready，候选需主动启用。译对复核空包的分类格保持空白，独立评阅仍为0。','']
    (output/'README.md').write_text('\n'.join(lines),'utf8')
    files={p.relative_to(output).as_posix():sha(p)for p in sorted(output.rglob('*'))if p.is_file()}
    write(output/'delivery_manifest.json',dict(schema_version=1,catalog_sha256=sha(catalog),files=files,source_pdf_included=False,student_data_included=False,external_calls=0,independent_annotation_records=0))
    archive=output.with_suffix('.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for p in sorted(output.rglob('*')):
            if p.is_file():
                item=zipfile.ZipInfo(p.relative_to(output).as_posix(),date_time=(2026,10,24,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.create_system=0;z.writestr(item,p.read_bytes(),compresslevel=6)
    return dict(directory=output.as_posix(),files_including_delivery_manifest=len(files)+1,zip=archive.as_posix(),zip_bytes=archive.stat().st_size,zip_sha256=sha(archive))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--catalog',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(build(a.catalog,a.output),ensure_ascii=False))
