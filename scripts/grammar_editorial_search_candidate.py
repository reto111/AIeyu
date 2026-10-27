"""Optional lexical query expansion candidate; frozen editions stay unchanged.

Rules map bounded Chinese descriptions to source topic headings, not answers.
The separate module instance prevents candidate topics leaking into baseline.
"""
import importlib.util
from pathlib import Path
import re

def load_local(name,filename):
 spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return module

lexical=load_local('_grammar_candidate_lexical','grammar_question_search.py')
rag=load_local('_grammar_candidate_rag','grammar_editorial_rag.py')
EXTRA_TOPICS=('不能使用副动词的情况','连接词概述')
lexical.TOPICS+=EXTRA_TOPICS

def expand_question(question):
 terms=[]
 if '名词' in question and re.search(r'临时|偶尔',question) and re.search(r'永久|长期',question):
  terms+=['词类转化','临时性转化','永久性转化']
 if '副动词' in question and (re.search(r'不同.{0,5}(?:主体|人|行为者)|不是同一个人|不能使用',question) or re.search(r'(?:主体|行为者).{0,4}不同',question)):
  terms+=['不能使用副动词的情况']
 if re.search(r'(?<![а-яё])о(?![а-яё])',question.lower()) and re.search(r'变体|元音|мне|обо',question.lower()):
  terms+=['原始前置词']
 if '连接词' in question and '前置词' in question and re.search(r'形式|变格',question):
  terms+=['连接词概述']
 if '谓语'in question and re.search(r'没有|无|不出现|省略|没有写出',question) and re.search(r'主语|我|你',question) and re.search(r'明确|确定|第一人称|第二人称',question):
  terms+=['确定人称句']
 if re.search(r'谓语|动词',question) and '复数'in question and re.search(r'不说明.{0,5}谁|不知道.{0,4}谁|不说谁|不明确.{0,5}行为者',question):
  terms+=['不定人称句']
 if re.search(r'呼唤|招呼',question) and re.search(r'句子成分|句首|句中|句尾|位置|其他成分',question):
  terms+=['呼语']
 return question+(' '+ ' '.join(dict.fromkeys(terms)) if terms else ''),terms

def search_question(question,limit=3,db=rag.DEFAULT_DB):
 if not isinstance(question,str)or not 1<=len(question.strip())<=2000:raise ValueError('Invalid question')
 expanded,aliases=expand_question(question)
 matches,terms=lexical.search_question(expanded,limit=limit,db=db)
 return matches,terms

# Only this private module object's retriever changes. Its source bindings,
# whole-section budgets and editorial evidence verification remain identical.
rag.search_question=search_question
def prepare(question,**kwargs):
 packet=rag.prepare(question,**kwargs)
 packet['candidate_query_expansions']=expand_question(question)[1]
 return packet
