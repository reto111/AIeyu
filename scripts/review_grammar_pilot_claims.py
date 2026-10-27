"""Source-relative assistant review of all 27 RAG claims; raw answers stay intact."""
import json
from collections import Counter
from grammar_editorial_guard import citation_contexts
from grammar_reference import strip_search_formatting
from run_grammar_generation_pilot import OUT, ROOT, write, now, digest

# Each judgment concerns the citations supplied with this individual claim,
# not facts supported elsewhere in the whole section or previous claims.
JUDGMENTS = {
 'P01': [('supported_by_quotes','基本通常中性及кофе阳性均有对应引句。'),
         ('needs_more_context','引用覆盖语言类概括与авеню，但未包含гоби及所列语言例名的具体原句。'),
         ('supported_by_quotes','通常规则与горячий кофе组合能支持核心，但5字规则引句不满足机械最短长度。')],
 'P02': [('supported_by_quotes','中心词原则与规范变化均有引句。'),
         ('supported_by_quotes','Министерство中性、趋向阳性及搭配均给出引句。'),
         ('needs_more_context','习用解释被引用，但БАМ等四例名称没有被该条引句实际列出。')],
 'P03': [('needs_more_context','同一格的表行在该来源中重复；缺表头与所讨论数词行，单看引句无法唯一绑定40/90/100。'),
         ('needs_more_context','引句给-а规律，未展示各词具体形式及重音；完整形式需结合变格表。'),
         ('needs_more_context','该条只引用сорок重音，未引用所列各格形式。')],
 'P04': [('supported_by_quotes','软硬两类由完整引句说明。'),
         ('needs_more_context','二三五六格引用齐全，第四格同一或二格的扩展缺该行引用。'),
         ('supported_by_quotes','与原书重音说明一致；该书对第四格的概括仍需结合动物性和同二格条件阅读，非通用规范背书。')],
 'P05': [('supported_by_quotes','无时式人称、有体原句支持。'),
         ('supported_by_quotes','两个不定式的体对立被直接引用。'),
         ('needs_more_context','引句只覆盖不定式未表时间人称，未覆盖читаю的式时人称数的完整对比。')],
 'P06': [('supported_by_quotes','历史两种记法与过去时词干к/г的原句均有。'),
         ('needs_more_context','引句仅说不分人称、分性数，未包含性数词尾细节。'),
         ('needs_more_context','引句有性数词尾，但本条“并非人称形式”的明确依据在上一条引句，需合并上下文或补引。')],
 'P07': [('supported_by_quotes','基本语义对比直接引用。'),
         ('needs_more_context','一般不可能用未完成体有引用，括注无对应体这一限定未包含在所截引句。'),
         ('needs_more_context','引句有反问例，但“实际暗含可以玩一玩”需补相邻解释；引句以“此时”起头存在上下文依赖。')],
 'P08': [('supported_by_quotes','第一分句完成体与第二分句按语义选体均在同一引句。'),
         ('needs_more_context','例句支持未完成体现在时，但一次具体结果通常倾向完成体是未单独引证的概括。'),
         ('uncited','原回答明确标作一般知识且无引用；不符合严格来源回答契约，不另行补造引用。')],
 'P09': [('supported_by_quotes','第一从句与удивилась对应关系直接引用。'),
         ('supported_by_quotes','意图表达的依附关系与源文一致，但引用把сказа́ла写成ска́зала，逐字规则失败。'),
         ('supported_by_quotes','不同词支配不同从句及主干都能定位；第二引句保留Markdown星号而不满足冻结的去格式规则。')]
}

def main():
    rows = []
    for path in sorted((OUT/'responses').glob('*_rag.json')):
        response = json.loads(path.read_text(encoding='utf-8'))
        cid = path.stem.split('_')[1]
        claims = response['parsed'].get('claims',[])
        if not claims:
            assert cid == 'P10'
            continue
        packet = json.loads((OUT/'packets'/f'{cid}.json').read_text(encoding='utf-8'))
        sources = {s['source_id']:s for s in packet['sources']}
        assert len(claims) == len(JUDGMENTS[cid])
        for index, (claim, judgment) in enumerate(zip(claims,JUDGMENTS[cid]),1):
            citations = []
            for citation in claim['citations']:
                source = sources[citation['source_id']]
                quote = citation['quote']
                citations.append({**citation, 'source_body_sha256':source['body_sha256'],
                    'content_kind':source['content_kind'],
                    'exact':quote in strip_search_formatting(source['body']),
                    'minimum_six_nonspace':len(''.join(quote.split())) >= 6,
                    **citation_contexts(source,quote)})
            rows.append({'case_id':cid,'claim_number':index,'original_text_zh':claim['text_zh'],
                'response_sha256':digest(path),'citation_support_judgment':judgment[0],
                'review_note':judgment[1],'citations':citations,
                'requires_independent_semantic_evaluation':True})
    assert len(rows) == 27
    summary = dict(Counter(r['citation_support_judgment'] for r in rows))
    write(ROOT/'data/processed/grammar_reference/reviews/pilot_claim_review_20261022_001.json',
        {'reviewed_at':now(),'scope':'all 27 claims in 9 substantive RAG answers; P10 refusal has no claims',
         'summary':summary,'claims':rows,'raw_responses_modified':False,'new_api_calls':0,
         'criteria':'逐条检查该主张实际提供的引句能否独立覆盖全部细节；缺上下文与事实错误分开。',
         'limits':['同一助手据来源复核，不是独立专家盲评或规范正确率。',
                   'needs_more_context不等于主张错误；原整节或其他主张的引句可能提供支持。',
                   '机械逐字引用与语义支持分别记录，不自动修复重音或替换原始回答。']})
    print(json.dumps({'reviewed_claims':27,'summary':summary},ensure_ascii=False))

if __name__ == '__main__':main()
