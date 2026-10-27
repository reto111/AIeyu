"""Keep the v2 gap evidence and add a separate lexical-list discovery queue."""
import argparse,json
from pathlib import Path
from build_aspect_inline_work_queue_v2 import build as build_v2

def build(roles,examples):
    result=build_v2(roles,examples)
    result['schema_version']=3
    for row in result['paragraphs']:
        row['lexical_list_priority']=bool(row['uncovered_russian_bearing_segments']) and row['paragraph_role']=='exposition_with_lexical_illustrations' and row['state']!='withheld'
    result['statistics']['lexical_list_priority_paragraphs']=sum(row['lexical_list_priority'] for row in result['paragraphs'])
    result['lexical_list_queue_definition_zh']='补充旧优先角色集合未包含的exposition_with_lexical_illustrations；只标记尚有未圈定俄文字母的非隔离段。可能是术语、回指或列举，不能据此自动增例或计剩余例数。旧两套优先标记和统计保持原口径。'
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--roles',type=Path,required=True);p.add_argument('--examples',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError('Immutable queue snapshot')
    result=build(a.roles,a.examples);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(result['statistics'],ensure_ascii=False))
