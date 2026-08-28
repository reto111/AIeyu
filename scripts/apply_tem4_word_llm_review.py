from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "processed" / "words" / "tem4_words_review_simple.csv"
DEFAULT_OUTPUT = DEFAULT_INPUT
DEFAULT_REVIEW_ONLY = ROOT / "data" / "processed" / "words" / "tem4_words_review_only.csv"
DEFAULT_REMOVED = ROOT / "data" / "processed" / "words" / "tem4_words_removed_by_llm.csv"
DEFAULT_REPORT = ROOT / "data" / "processed" / "words" / "tem4_words_llm_review_report.json"


# These decisions are tied to the OCR page/block coordinates so that a later
# re-extraction cannot silently apply a correction to a different entry.
DECISIONS: dict[tuple[str, str], dict[str, str]] = {
    ("7", "1"): {"status": "rejected", "note": "book_heading_not_a_word"},
    ("10", "4"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("11", "2"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("11", "13"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("18", "2"): {"status": "rejected", "note": "example_sentence_not_headword"},
    ("24", "2"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("25", "10"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("27", "2"): {"word": "в", "meaning_zh": "到；往；向；在；成为；（表示数量、时间等关系）", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("34", "12"): {"word": "вид", "meaning_zh": "外貌；样子；形式；种类；（语法）体；景色，景象", "status": "approved", "note": "ocr_i_and_n_shape_correction"},
    ("45", "11"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("48", "12"): {"word": "вы", "meaning_zh": "您；你们", "status": "approved", "note": "ocr_y_shape_correction"},
    ("56", "7"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("59", "2"): {"status": "rejected", "note": "example_sentence_not_headword"},
    ("63", "4"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("70", "7"): {"status": "rejected", "note": "example_sentence_not_headword"},
    ("74", "9"): {"word": "для", "meaning_zh": "为了；给；对……来说；用于", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("75", "3"): {"word": "прикоснуться", "meaning_zh": "碰到；接触；触摸", "status": "approved", "note": "ocr_headword_recovered_from_infinitive_and_meaning"},
    ("77", "4"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("83", "13"): {"status": "rejected", "note": "example_sentence_not_headword"},
    ("87", "6"): {"word": "жизнь", "meaning_zh": "生命；生活；一生；生平", "status": "approved", "note": "ocr_headword_recovered_from_meaning"},
    ("91", "11"): {"word": "заказать", "meaning_zh": "订购；预订；定做", "status": "approved", "note": "ocr_headword_recovered_from_examples"},
    ("108", "7"): {"word": "или", "meaning_zh": "或；或者；还是；即……也……", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("108", "11"): {"status": "rejected", "note": "inflection_label_and_collocations_not_headword"},
    ("113", "3"): {"word": "их", "meaning_zh": "他们的；她们的；它们的", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("113", "7"): {"word": "к", "meaning_zh": "向；朝；往；到；对于", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("117", "5"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("118", "8"): {"word": "киоск", "meaning_zh": "售货亭；报刊亭；小摊亭", "status": "approved", "note": "ocr_b_and_g_shape_correction"},
    ("124", "15"): {"word": "коренной", "meaning_zh": "根本的；基本的；主要的；本地的（如 коренной москвич）", "status": "approved", "note": "ocr_headword_recovered_from_raw_entry"},
    ("125", "5"): {"word": "кормить", "meaning_zh": "喂养；给……吃；供养；赡养", "status": "approved", "note": "ocr_headword_recovered_from_infinitive"},
    ("130", "2"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("133", "1"): {"status": "rejected", "note": "page_number_or_layout_noise"},
    ("134", "1"): {"word": "лишать", "lemma": "лишать", "part_of_speech": "未", "meaning_zh": "剥夺……的权利；使……失去……（完成体：лишить）", "status": "approved", "note": "user_confirmed_lishat_and_lishit_aspect_pair"},
    ("138", "2"): {"status": "rejected", "note": "fixed_expression_not_single_headword"},
    ("143", "6"): {"status": "needs_review", "note": "headword_missing_cannot_reliably_recover_from_meaning_only"},
    ("148", "2"): {"word": "мыслить", "meaning_zh": "思考；想；认为", "status": "approved", "note": "ocr_headword_recovered_from_collocations"},
    ("152", "6"): {"word": "наизусть", "meaning_zh": "熟记；背熟；凭记忆", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("154", "2"): {"remove": "true", "status": "rejected", "note": "user_confirmed_unrecoverable_ocr"},
    ("159", "3"): {"word": "по-русски", "meaning_zh": "用俄语；俄语地", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("167", "2"): {"word": "облик", "meaning_zh": "外貌；面貌；形象；景象", "status": "approved", "note": "ocr_o_and_b_shape_correction"},
    ("209", "8"): {"word": "поливать", "meaning_zh": "浇水；浇灌；（液体）洒到或冲到", "status": "approved", "note": "ocr_headword_recovered_from_raw_entry"},
    ("210", "3"): {"status": "rejected", "note": "example_sentence_not_headword"},
    ("211", "6"): {"status": "rejected", "note": "fixed_expression_not_single_headword"},
    ("211", "7"): {"status": "rejected", "note": "fragment_of_fixed_expression"},
    ("230", "11"): {"word": "разрешить", "meaning_zh": "解决；处理；允许；准许", "status": "approved", "note": "ocr_headword_recovered_from_infinitive"},
    ("234", "2"): {"status": "rejected", "note": "collocation_not_headword"},
    ("243", "2"): {"word": "раз", "meaning_zh": "一次；一回；既然；既然如此", "status": "approved", "note": "ocr_headword_recovered_from_conjunction_example"},
    ("243", "11"): {"word": "разведчик", "meaning_zh": "侦察员；侦察兵；情报员", "status": "approved", "note": "ocr_headword_recovered_from_meaning_and_example"},
    ("244", "8"): {"word": "разговаривать", "meaning_zh": "谈话；交谈；说话", "status": "approved", "note": "ocr_headword_recovered_from_infinitive"},
    ("251", "10"): {"word": "борьба", "meaning_zh": "斗争；战斗；搏斗；竞争", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("256", "2"): {"status": "rejected", "note": "fixed_expression_not_single_headword"},
    ("261", "10"): {"word": "выпустить", "meaning_zh": "放出；释放；发行；生产或出版", "status": "approved", "note": "ocr_headword_recovered_from_infinitive"},
    ("275", "7"): {"word": "собственность", "meaning_zh": "所有权；财产；所有物", "status": "approved", "note": "ocr_digit_and_latin_shape_correction"},
    ("278", "5"): {"word": "создать", "meaning_zh": "创造；创作；建立；造成", "status": "approved", "note": "ocr_headword_recovered_from_infinitive"},
    ("278", "6"): {"status": "rejected", "note": "duplicate_continuation_of_create_entry"},
    ("278", "12"): {"word": "сознательный", "meaning_zh": "有意识的；自觉的；故意的", "status": "approved", "note": "ocr_headword_recovered_from_sentence"},
    ("281", "10"): {"word": "состояние", "meaning_zh": "状态；状况；形势；心情；财产状况", "status": "approved", "note": "ocr_headword_recovered_from_meaning"},
    ("290", "3"): {"word": "стиль", "meaning_zh": "风格；文体；样式；（历法）历法", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("290", "5"): {"word": "стих", "meaning_zh": "诗；诗歌；诗句", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("290", "8"): {"word": "стоить", "meaning_zh": "值；花费；值得", "status": "approved", "note": "ocr_headword_confirmed_from_conjugation"},
    ("293", "16"): {"word": "стул", "meaning_zh": "椅子；凳子", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("295", "1"): {"status": "rejected", "note": "page_number_or_layout_noise"},
    ("298", "9"): {"word": "танец", "meaning_zh": "舞蹈；舞；舞会（复数 танцы）", "status": "approved", "note": "ocr_headword_recovered_from_collocations"},
    ("307", "9"): {"word": "требовать", "meaning_zh": "要求；需要；索要；召唤", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("314", "11"): {"word": "удобство", "meaning_zh": "舒适；方便；便利；方便设施", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("315", "1"): {"status": "rejected", "note": "page_number_or_layout_noise"},
    ("315", "11"): {"word": "узкий", "meaning_zh": "狭窄的；窄的；有限的；狭义的", "status": "approved", "note": "ocr_headword_recovered_from_definition"},
    ("325", "13"): {"word": "форма", "meaning_zh": "形式；形状；制服；表格", "status": "approved", "note": "ocr_headword_recovered_from_collocations"},
    ("326", "6"): {"word": "фронт", "meaning_zh": "前线；战线；统一战线；（转）活动领域", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("332", "2"): {"word": "центральный", "part_of_speech": "形", "meaning_zh": "中心的；中央的；核心的；中央空调、集中供暖、中央委员会、中心思想等", "status": "approved", "note": "user_confirmed_headword_from_adjacent_page"},
    ("340", "1"): {"status": "rejected", "note": "page_number_or_layout_noise"},
    ("342", "3"): {"word": "экономия", "meaning_zh": "节约；节省；节约的办法；经济（学）", "status": "approved", "note": "ocr_o_and_b_shape_correction"},
    ("346", "10"): {"word": "отложить", "meaning_zh": "推迟；延期；搁置；把……放到一边", "status": "approved", "note": "ocr_headword_recovered_from_infinitive"},
    ("350", "1"): {"word": "капля в море", "part_of_speech": "固定结构", "meaning_zh": "沧海一粟；微不足道的一小部分", "status": "approved", "note": "ocr_b_to_v_and_m6pe_to_more_recovered_from_idiom"},
}


PENDING_BATCH1_DECISIONS: dict[tuple[str, str], dict[str, str]] = {
    ("8", "1"): {"status": "rejected", "note": "book_heading_not_a_word"},
    ("8", "2"): {"word": "а", "part_of_speech": "连", "meaning_zh": "啊；而；但是", "status": "approved", "note": "llm_verified_function_word"},
    ("8", "3"): {"meaning_zh": "段落；（文章的）一段", "status": "approved", "note": "llm_verified_core_meaning"},
    ("8", "4"): {"meaning_zh": "事故；失事；故障；（转）失败", "status": "approved", "note": "llm_verified_core_meaning"},
    ("8", "5"): {"meaning_zh": "八月", "status": "approved", "note": "llm_verified_core_meaning"},
    ("8", "6"): {"meaning_zh": "航空邮件", "status": "approved", "note": "llm_verified_core_meaning"},
    ("8", "7"): {"meaning_zh": "航空；航空兵；航空学", "status": "approved", "note": "llm_verified_core_meaning"},
    ("8", "8"): {"meaning_zh": "公共汽车；大客车", "status": "approved", "note": "llm_verified_core_meaning"},
    ("8", "9"): {"meaning_zh": "自动机；自动装置；自动枪；自动电话", "status": "approved", "note": "llm_verified_core_meaning"},
    ("9", "1"): {"status": "rejected", "note": "continuation_fragment_of_previous_entry"},
    ("9", "2"): {"meaning_zh": "自动的；无意识的；机械的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("9", "3"): {"word": "автомобиль", "lemma": "автомобиль", "meaning_zh": "汽车；车辆；轿车；卡车等机动车", "status": "approved", "note": "llm_recovered_headword_from_definition"},
    ("9", "4"): {"meaning_zh": "自治的；有自治权的；自主的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("9", "5"): {"meaning_zh": "作者；作家；发明人；创始人", "status": "approved", "note": "llm_verified_core_meaning"},
    ("9", "6"): {"word": "авторитет", "lemma": "авторитет", "meaning_zh": "威信；威望；权威；权威人士", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("9", "7"): {"word": "агентство", "lemma": "агентство", "meaning_zh": "代理处；办事处；通讯社；机构", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("9", "8"): {"word": "агрессия", "lemma": "агрессия", "meaning_zh": "侵略；侵略行为；侵略性", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("9", "9"): {"meaning_zh": "农学家；农艺师；农业技术员", "status": "approved", "note": "llm_verified_core_meaning"},
    ("9", "10"): {"meaning_zh": "行政管理机关；行政管理人员", "status": "approved", "note": "llm_verified_core_meaning"},
    ("9", "11"): {"meaning_zh": "地址；住址；致……的；对……来说", "status": "approved", "note": "llm_verified_core_meaning"},
    ("10", "2"): {"word": "академик", "lemma": "академик", "meaning_zh": "科学院院士；学者", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("10", "3"): {"word": "академия", "lemma": "академия", "meaning_zh": "科学院；学院；大学", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("10", "5"): {"meaning_zh": "认真的；准时的；整洁的；仔细的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("10", "6"): {"meaning_zh": "积极的；主动的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("10", "7"): {"part_of_speech": "形", "meaning_zh": "迫切的；切合现实的；实际的", "status": "approved", "note": "llm_corrected_pos_and_core_meaning"},
    ("10", "8"): {"meaning_zh": "纪念册；相册；画册；图集", "status": "approved", "note": "llm_verified_core_meaning"},
    ("10", "9"): {"meaning_zh": "登山运动", "status": "approved", "note": "llm_verified_core_meaning"},
    ("10", "10"): {"meaning_zh": "美国人；美籍华人", "status": "approved", "note": "llm_verified_core_meaning"},
    ("10", "11"): {"meaning_zh": "美洲（人）的；美国（人）的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("10", "12"): {"meaning_zh": "分析；分析研究", "status": "approved", "note": "llm_verified_core_meaning"},
    ("10", "13"): {"meaning_zh": "英国（人）的；英语的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("10", "14"): {"meaning_zh": "英国人", "status": "approved", "note": "llm_verified_core_meaning"},
    ("10", "15"): {"word": "анкета", "lemma": "анкета", "part_of_speech": "阴", "meaning_zh": "问卷；履历表；登记表；表格", "status": "approved", "note": "llm_corrected_pos_and_core_meaning"},
    ("11", "3"): {"meaning_zh": "橙子；橙树", "status": "approved", "note": "llm_verified_core_meaning"},
    ("11", "4"): {"meaning_zh": "鼓掌；拍手", "status": "approved", "note": "llm_verified_core_meaning"},
    ("11", "5"): {"word": "аплодисменты", "lemma": "аплодисменты", "meaning_zh": "掌声；鼓掌", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("11", "6"): {"meaning_zh": "器械；仪器；装置；机关；部门", "status": "approved", "note": "llm_verified_core_meaning"},
    ("11", "7"): {"word": "аппетит", "lemma": "аппетит", "meaning_zh": "食欲；胃口", "status": "approved", "note": "llm_recovered_headword_from_definition"},
    ("11", "8"): {"word": "апрель", "lemma": "апрель", "meaning_zh": "四月", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("11", "9"): {"word": "аптека", "lemma": "аптека", "meaning_zh": "药店；配药室", "status": "approved", "note": "llm_recovered_headword_from_definition"},
    ("11", "10"): {"meaning_zh": "西瓜", "status": "approved", "note": "llm_verified_core_meaning"},
    ("11", "11"): {"meaning_zh": "逮捕；查封；没收", "status": "approved", "note": "llm_verified_core_meaning"},
    ("11", "12"): {"meaning_zh": "军队；军团", "status": "approved", "note": "llm_verified_core_meaning"},
    ("12", "1"): {"status": "rejected", "note": "continuation_fragment_of_next_entry"},
    ("12", "2"): {"meaning_zh": "演员；艺人；杂技演员", "status": "approved", "note": "llm_verified_core_meaning"},
    ("12", "3"): {"word": "архитектура", "lemma": "архитектура", "meaning_zh": "建筑艺术；建筑学；建筑风格", "status": "approved", "note": "llm_corrected_ocr_headword"},
    ("12", "4"): {"meaning_zh": "博士研究生；研究生", "status": "approved", "note": "llm_verified_core_meaning"},
    ("12", "5"): {"meaning_zh": "副博士研究生班；副博士研究生学历", "status": "approved", "note": "llm_verified_core_meaning"},
    ("12", "6"): {"status": "rejected", "note": "example_sentence_fragment"},
    ("12", "7"): {"meaning_zh": "进攻；袭击；（转）攻击", "status": "approved", "note": "llm_verified_core_meaning"},
    ("12", "8"): {"word": "атлетика", "lemma": "атлетика", "meaning_zh": "竞技运动；田径运动", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("12", "9"): {"word": "атмосфера", "lemma": "атмосфера", "meaning_zh": "大气；大气层；气氛；环境；大气压", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("12", "10"): {"meaning_zh": "原子的；利用原子能的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("12", "11"): {"meaning_zh": "毕业证书；文凭", "status": "approved", "note": "llm_verified_core_meaning"},
    ("12", "12"): {"word": "аудитория", "lemma": "аудитория", "meaning_zh": "讲堂；（大学的）教室；听众；学生", "status": "approved", "note": "llm_recovered_headword_from_definition"},
    ("12", "13"): {"meaning_zh": "广告；海报（戏剧、电影、音乐会等）", "status": "approved", "note": "llm_verified_core_meaning"},
    ("12", "14"): {"status": "rejected", "note": "continuation_fragment_of_afisha_entry"},
    ("12", "15"): {"meaning_zh": "飞机场；机场", "status": "approved", "note": "llm_verified_core_meaning"},
    ("12", "16"): {"word": "аэропорт", "lemma": "аэропорт", "meaning_zh": "机场；航空站", "status": "approved", "note": "llm_corrected_ocr_headword"},
    ("13", "1"): {"status": "rejected", "note": "continuation_fragment_of_babushka_entry"},
    ("13", "2"): {"meaning_zh": "祖母；外祖母；老太婆；老大娘", "status": "approved", "note": "llm_verified_core_meaning"},
    ("13", "3"): {"meaning_zh": "行李；行李物品", "status": "approved", "note": "llm_verified_core_meaning"},
    ("13", "4"): {"part_of_speech": "阴", "meaning_zh": "基础；柱脚；根据；基地；服务站", "status": "approved", "note": "llm_corrected_pos_and_core_meaning"},
    ("13", "5"): {"meaning_zh": "集市；市场", "status": "approved", "note": "llm_verified_core_meaning"},
    ("13", "6"): {"meaning_zh": "芭蕾舞女演员；女舞蹈家", "status": "approved", "note": "llm_verified_core_meaning"},
    ("13", "7"): {"word": "балет", "lemma": "балет", "meaning_zh": "芭蕾舞；芭蕾舞剧", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("13", "8"): {"meaning_zh": "阳台；凉台；（剧场的）楼座", "status": "approved", "note": "llm_verified_core_meaning"},
    ("13", "9"): {"word": "банан", "lemma": "банан", "meaning_zh": "香蕉；芭蕉", "status": "approved", "note": "llm_corrected_ocr_headword"},
    ("13", "10"): {"meaning_zh": "银行；数据库；人才库；基因库", "status": "approved", "note": "llm_verified_core_meaning"},
    ("13", "11"): {"meaning_zh": "澡堂；浴室；浴池；桑拿浴", "status": "approved", "note": "llm_verified_core_meaning"},
    ("14", "1"): {"status": "rejected", "note": "continuation_fragment_of_bedstvie_entry"},
    ("14", "2"): {"meaning_zh": "篮球；篮球运动", "status": "approved", "note": "llm_verified_core_meaning"},
    ("14", "3"): {"meaning_zh": "寓言；寓言故事", "status": "approved", "note": "llm_verified_core_meaning"},
    ("14", "4"): {"word": "бассейн", "lemma": "бассейн", "meaning_zh": "水池；蓄水池；游泳池；（江、湖等的）流域", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("14", "5"): {"meaning_zh": "塔；塔楼", "status": "approved", "note": "llm_verified_core_meaning"},
    ("14", "6"): {"meaning_zh": "警惕性；警戒；警觉", "status": "approved", "note": "llm_verified_core_meaning"},
    ("14", "7"): {"meaning_zh": "跑步；赛跑", "status": "approved", "note": "llm_verified_core_meaning"},
    ("14", "8"): {"word": "бегать", "lemma": "бегать", "meaning_zh": "跑；奔跑；逃跑；躲避", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("14", "9"): {"word": "беда", "lemma": "беда", "meaning_zh": "不幸；灾难；倒霉事", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("14", "10"): {"word": "бедный", "lemma": "бедный", "meaning_zh": "贫穷的；贫乏的；可怜的；不幸的", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("14", "11"): {"word": "бедствие", "lemma": "бедствие", "meaning_zh": "灾祸；灾难", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("15", "2"): {"meaning_zh": "跑；奔跑；急驶；流逝；流动", "status": "approved", "note": "llm_verified_core_meaning"},
    ("15", "3"): {"word": "без", "lemma": "без", "part_of_speech": "前", "meaning_zh": "没有；无；不在；缺少；差……（时间、数量）", "status": "approved", "note": "llm_recovered_preposition_from_layout"},
    ("15", "4"): {"meaning_zh": "无边际的；无限的；无穷的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("15", "5"): {"word": "безобразие", "lemma": "безобразие", "meaning_zh": "丑陋；可恶的现象；不成体统的行为", "status": "approved", "note": "llm_recovered_headword_from_russian_example"},
    ("15", "6"): {"meaning_zh": "安全；无危险", "status": "approved", "note": "llm_verified_core_meaning"},
    ("15", "7"): {"meaning_zh": "失业；失业现象；失业状态", "status": "approved", "note": "llm_verified_core_meaning"},
    ("15", "8"): {"meaning_zh": "无条件地；绝对；毫无疑问；当然", "status": "approved", "note": "llm_verified_core_meaning"},
    ("15", "9"): {"meaning_zh": "白俄罗斯人", "status": "approved", "note": "llm_verified_core_meaning"},
    ("15", "10"): {"word": "белый", "lemma": "белый", "meaning_zh": "白色的；白的；白种人的；白军的；白党的", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("16", "1"): {"status": "rejected", "note": "continuation_fragment_of_previous_entry"},
    ("16", "2"): {"word": "бельё", "lemma": "бельё", "meaning_zh": "内衣；（床单、桌布等）家用布品", "status": "approved", "note": "llm_verified_real_yo"},
    ("16", "3"): {"meaning_zh": "汽油", "status": "approved", "note": "llm_verified_core_meaning"},
    ("16", "4"): {"word": "берег", "lemma": "берег", "meaning_zh": "岸；海岸；陆地；对岸", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("16", "5"): {"word": "берёза", "lemma": "берёза", "meaning_zh": "桦树；白桦树", "status": "approved", "note": "llm_verified_real_yo"},
    ("16", "6"): {"word": "беречь", "lemma": "беречь", "meaning_zh": "保存；珍藏；节省；爱惜；爱护", "status": "approved", "note": "llm_verified_real_yo"},
    ("16", "7"): {"word": "беседа", "lemma": "беседа", "meaning_zh": "交谈；会谈；谈心；座谈会", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("16", "8"): {"word": "беседовать", "lemma": "беседовать", "meaning_zh": "交谈；交换意见；倾谈", "status": "approved", "note": "llm_verified_core_meaning"},
    ("16", "9"): {"word": "бесконечный", "lemma": "бесконечный", "meaning_zh": "无限的；无穷的；漫长的；无休止的", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("16", "10"): {"meaning_zh": "免费的；无报酬的", "status": "approved", "note": "llm_verified_core_meaning"},
}


PENDING_BATCH2_DECISIONS: dict[tuple[str, str], dict[str, str]] = {
    ("16", "11"): {"word": "беспокоить", "lemma": "беспокоить", "meaning_zh": "打扰；使担心；使不安", "status": "approved", "note": "llm_corrected_ocr_headword"},
    ("16", "12"): {"meaning_zh": "担心；不安；费心；劳神", "status": "approved", "note": "llm_verified_core_meaning"},
    ("17", "2"): {"meaning_zh": "无能为力的；孤立无援的；软弱的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("17", "3"): {"meaning_zh": "无秩序；混乱；骚乱", "status": "approved", "note": "llm_verified_core_meaning"},
    ("17", "4"): {"meaning_zh": "无情的；残酷的；极度的（严寒等）", "status": "approved", "note": "llm_reconstructed_split_entry"},
    ("17", "5"): {"status": "rejected", "note": "continuation_fragment_of_besposhchadny_entry"},
    ("17", "6"): {"word": "бессмертный", "lemma": "бессмертный", "meaning_zh": "不死的；永生的；不朽的", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("17", "7"): {"word": "библиотека", "lemma": "библиотека", "meaning_zh": "图书馆；藏书；藏书室", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("17", "8"): {"word": "билет", "lemma": "билет", "meaning_zh": "票；券；证件；考试题签", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("17", "9"): {"meaning_zh": "个人经历；履历；传记；生平", "status": "approved", "note": "llm_verified_core_meaning"},
    ("17", "10"): {"meaning_zh": "生物学", "status": "approved", "note": "llm_verified_core_meaning"},
    ("17", "11"): {"meaning_zh": "会战；交战；战役", "status": "approved", "note": "llm_verified_core_meaning"},
    ("17", "12"): {"meaning_zh": "打；敲；拍打；打破", "status": "approved", "note": "llm_verified_core_meaning"},
    ("17", "13"): {"meaning_zh": "作战；厮打；碰撞；挣扎；（心脏等）跳动", "status": "approved", "note": "llm_verified_core_meaning"},
    ("18", "3"): {"meaning_zh": "感谢；致谢", "status": "approved", "note": "llm_verified_core_meaning"},
    ("18", "4"): {"part_of_speech": "阴", "meaning_zh": "谢意；感激；感谢；表扬", "status": "approved", "note": "llm_corrected_pos_and_core_meaning"},
    ("18", "5"): {"word": "благодарный", "lemma": "благодарный", "meaning_zh": "感谢的；感激的", "status": "approved", "note": "llm_removed_grammar_tail"},
    ("18", "6"): {"part_of_speech": "前", "meaning_zh": "由于；多亏", "status": "approved", "note": "llm_corrected_pos_and_core_meaning"},
    ("18", "7"): {"meaning_zh": "平安地；顺利地", "status": "approved", "note": "llm_verified_core_meaning"},
    ("18", "8"): {"meaning_zh": "有利的；有助于……的；良好的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("18", "9"): {"meaning_zh": "高尚的；崇高的；贵族的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("18", "10"): {"word": "бледный", "lemma": "бледный", "meaning_zh": "苍白的；暗淡的；平淡的", "status": "approved", "note": "llm_removed_grammar_tail"},
    ("18", "11"): {"word": "блестеть", "lemma": "блестеть", "meaning_zh": "发光；闪耀；闪闪发光", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("18", "12"): {"meaning_zh": "闪耀；一闪；显现；表现出众", "status": "approved", "note": "llm_verified_core_meaning"},
    ("19", "1"): {"status": "rejected", "note": "continuation_fragment_of_blestyashchiy_entry"},
    ("19", "2"): {"meaning_zh": "闪光的；辉煌的；卓越的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("19", "3"): {"meaning_zh": "近的；临近的；亲近的；关系密切的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("19", "4"): {"meaning_zh": "包围；封锁", "status": "approved", "note": "llm_verified_core_meaning"},
    ("19", "5"): {"meaning_zh": "盘子；菜肴；一道菜", "status": "approved", "note": "llm_verified_core_meaning"},
    ("19", "6"): {"word": "бог", "lemma": "бог", "meaning_zh": "上帝；天主", "status": "approved", "note": "llm_recovered_headword_from_meaning"},
    ("19", "7"): {"meaning_zh": "财富；丰富；资源库", "status": "approved", "note": "llm_verified_core_meaning"},
    ("19", "8"): {"meaning_zh": "富有的；丰富的；含有丰富……的；富人", "status": "approved", "note": "llm_verified_core_meaning"},
    ("19", "9"): {"meaning_zh": "精力充沛的；精神饱满的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("19", "10"): {"meaning_zh": "战斗的；作战的；战斗精神的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("19", "11"): {"word": "боец", "lemma": "боец", "meaning_zh": "战士；战斗员；搏击运动员", "status": "approved", "note": "llm_recovered_headword_from_meaning"},
    ("20", "2"): {"meaning_zh": "战斗；战役", "status": "approved", "note": "llm_verified_core_meaning"},
    ("20", "3"): {"meaning_zh": "肋部；侧面；旁边；并肩地", "status": "approved", "note": "llm_verified_core_meaning"},
    ("20", "4"): {"meaning_zh": "拳击；拳术", "status": "approved", "note": "llm_verified_core_meaning"},
    ("20", "5"): {"meaning_zh": "多于；超过；更加", "status": "approved", "note": "llm_verified_core_meaning"},
    ("20", "6"): {"word": "болезнь", "lemma": "болезнь", "meaning_zh": "疾病；病；病症", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("20", "7"): {"meaning_zh": "生病；疼痛；支持（球队等）", "status": "approved", "note": "llm_merged_homonymous_entry_meanings"},
    ("20", "8"): {"status": "rejected", "note": "duplicate_continuation_of_bolyet_entry"},
    ("20", "9"): {"meaning_zh": "闲扯；乱说；说走嘴；泄露", "status": "approved", "note": "llm_verified_core_meaning"},
    ("20", "10"): {"meaning_zh": "疼痛；痛苦；悲痛", "status": "approved", "note": "llm_verified_core_meaning"},
    ("21", "1"): {"status": "rejected", "note": "continuation_fragment_of_previous_entry"},
    ("21", "2"): {"meaning_zh": "医院；病院", "status": "approved", "note": "llm_verified_core_meaning"},
    ("21", "3"): {"meaning_zh": "痛地；疼痛；痛心；难过", "status": "approved", "note": "llm_verified_core_meaning"},
    ("21", "4"): {"word": "больной", "lemma": "больной", "meaning_zh": "有病的；病人；痛处；棘手的问题", "status": "approved", "note": "llm_recovered_headword_from_meaning"},
    ("21", "5"): {"meaning_zh": "再也（不）；大于；多于；更加", "status": "approved", "note": "llm_verified_core_meaning"},
    ("21", "6"): {"meaning_zh": "多数；大多数", "status": "approved", "note": "llm_verified_core_meaning"},
    ("21", "7"): {"meaning_zh": "大的；很大的；成年的；很多的；流行的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("21", "9"): {"status": "rejected", "note": "continuation_fragment_of_bolshoy_entry"},
    ("22", "1"): {"status": "rejected", "note": "continuation_fragment_of_bolshoy_entry"},
    ("22", "2"): {"meaning_zh": "炸弹；原子弹；氢弹", "status": "approved", "note": "llm_verified_core_meaning"},
    ("22", "3"): {"word": "борец", "lemma": "борец", "meaning_zh": "斗士；战士；摔跤运动员", "status": "approved", "note": "llm_recovered_headword_from_russian_example"},
    ("22", "4"): {"meaning_zh": "胡子；胡须", "status": "approved", "note": "llm_verified_core_meaning"},
    ("22", "5"): {"meaning_zh": "斗争；奋战；为……而奋斗；冲突", "status": "approved", "note": "llm_verified_core_meaning"},
    ("22", "6"): {"meaning_zh": "船舷；船上；（船、飞机、宇宙飞船）上", "status": "approved", "note": "llm_verified_core_meaning"},
    ("22", "7"): {"meaning_zh": "摔跤；斗争；战斗；竞争", "status": "approved", "note": "llm_verified_core_meaning"},
    ("22", "8"): {"meaning_zh": "赤脚的；光脚的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("22", "9"): {"meaning_zh": "鞋；靴子（复数）", "status": "approved", "note": "llm_verified_core_meaning"},
    ("22", "10"): {"meaning_zh": "害怕；怕；经受不住", "status": "approved", "note": "llm_reconstructed_split_entry"},
    ("23", "1"): {"status": "rejected", "note": "continuation_fragment_of_boyatsya_entry"},
    ("23", "2"): {"word": "брак", "lemma": "брак", "part_of_speech": "阳", "meaning_zh": "婚姻；结婚；婚姻关系；废品；产品瑕疵", "status": "approved", "note": "llm_recovered_split_headword_and_merged_meanings"},
    ("23", "3"): {"status": "rejected", "note": "fixed_expression_not_headword"},
    ("23", "4"): {"meaning_zh": "兄弟；哥哥；弟弟；老兄；老弟", "status": "approved", "note": "llm_verified_core_meaning"},
    ("23", "5"): {"status": "rejected", "note": "example_sentence_fragment"},
    ("23", "6"): {"meaning_zh": "兄弟的；兄弟般的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("23", "7"): {"meaning_zh": "拿；取；带；承担；乘坐；攻取；抓住；控制", "status": "approved", "note": "llm_merged_aspect_entry_meanings"},
    ("23", "8"): {"status": "rejected", "note": "continuation_fragment_of_brat_entry"},
    ("23", "9"): {"status": "rejected", "note": "example_sentence_fragment"},
    ("23", "10"): {"part_of_speech": "未", "meaning_zh": "抓住；握住；着手做；开始；承担；担任", "status": "approved", "note": "llm_corrected_pos_and_core_meaning"},
    ("23", "11"): {"meaning_zh": "队；组；工作队；旅（运输等）", "status": "approved", "note": "llm_verified_core_meaning"},
    ("24", "1"): {"status": "rejected", "note": "continuation_fragment_of_brov_entry"},
    ("24", "3"): {"word": "бросать", "lemma": "бросать", "meaning_zh": "扔；投；抛弃；戒掉；放弃；突然出现；挥霍；责难", "status": "approved", "note": "llm_corrected_ocr_headword"},
    ("24", "4"): {"meaning_zh": "互相投掷；扑向；纵身跳下；引人注目；刺鼻", "status": "approved", "note": "llm_verified_core_meaning"},
    ("24", "5"): {"part_of_speech": "复", "meaning_zh": "裤子", "status": "approved", "note": "llm_corrected_pos_and_core_meaning"},
    ("24", "6"): {"word": "будильник", "lemma": "будильник", "meaning_zh": "闹钟；闹铃", "status": "approved", "note": "llm_recovered_headword_from_raw_block"},
    ("24", "7"): {"meaning_zh": "叫醒；唤醒；引起（兴趣、好奇心等）", "status": "approved", "note": "llm_verified_core_meaning"},
    ("24", "8"): {"meaning_zh": "好像；似乎", "status": "approved", "note": "llm_verified_core_meaning"},
    ("25", "1"): {"status": "rejected", "note": "continuation_fragment_of_budto_entry"},
    ("25", "2"): {"meaning_zh": "将来的；未来的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("25", "3"): {"meaning_zh": "字母；文字；一字；（引申）原文、字面", "status": "approved", "note": "llm_verified_core_meaning"},
    ("25", "4"): {"word": "бумага", "lemma": "бумага", "meaning_zh": "纸；文件；公文；证券；有价证券", "status": "approved", "note": "llm_corrected_ocr_headword"},
    ("25", "5"): {"meaning_zh": "资产阶级", "status": "approved", "note": "llm_verified_core_meaning"},
    ("25", "6"): {"meaning_zh": "资产阶级的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("25", "7"): {"meaning_zh": "汹涌的；猛烈的；蓬勃的；飞速的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("25", "8"): {"meaning_zh": "暴风雨；风暴；热潮；风波", "status": "approved", "note": "llm_verified_core_meaning"},
    ("25", "9"): {"meaning_zh": "瓶；（玻璃）瓶", "status": "approved", "note": "llm_verified_core_meaning"},
    ("25", "11"): {"word": "буфет", "lemma": "буфет", "meaning_zh": "茶点部；小卖部；小吃部", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("26", "2"): {"meaning_zh": "要是；若是；最好；就好了；但愿", "status": "approved", "note": "llm_verified_core_meaning"},
    ("26", "3"): {"meaning_zh": "有；存在；常去；往往是；有时是", "status": "approved", "note": "llm_verified_core_meaning"},
    ("26", "4"): {"meaning_zh": "原先的；以前的；前任的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("26", "5"): {"meaning_zh": "公牛；雄牛", "status": "approved", "note": "llm_verified_core_meaning"},
    ("26", "6"): {"meaning_zh": "快的；迅速的；敏捷的；机灵的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("26", "7"): {"word": "быт", "lemma": "быт", "meaning_zh": "日常生活；生活方式；生活习惯", "status": "approved", "note": "llm_recovered_headword_from_raw_block"},
    ("26", "8"): {"part_of_speech": "未", "meaning_zh": "是；有；存在；处在；发生；成为", "status": "approved", "note": "llm_verified_core_meaning"},
}


PENDING_BATCH3_DECISIONS: dict[tuple[str, str], dict[str, str]] = {
    ("21", "6"): {"word": "большевик", "lemma": "большевик", "part_of_speech": "阳", "meaning_zh": "布尔什维克", "status": "approved", "note": "llm_coordinate_correction"},
    ("21", "7"): {"word": "большинство", "lemma": "большинство", "part_of_speech": "中", "meaning_zh": "多数；大多数", "status": "approved", "note": "llm_coordinate_correction"},
    ("21", "8"): {"meaning_zh": "大的；很大的；成年的；很多的；流行的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("23", "12"): {"meaning_zh": "（给自己）刮脸；剃须", "status": "approved", "note": "llm_verified_core_meaning"},
    ("23", "13"): {"meaning_zh": "眉毛；眉", "status": "approved", "note": "llm_verified_core_meaning"},
    ("26", "9"): {"status": "rejected", "note": "continuation_fragment_of_byt_entry"},
    ("26", "10"): {"word": "бюро", "lemma": "бюро", "part_of_speech": "中，不变", "meaning_zh": "局；处；所；（某些机构的）领导机构", "status": "approved", "note": "llm_corrected_ocr_headword"},
    ("27", "3"): {"meaning_zh": "（火车或电车的）车厢", "status": "approved", "note": "llm_verified_core_meaning"},
    ("27", "4"): {"meaning_zh": "重要；举止傲慢", "status": "approved", "note": "llm_verified_core_meaning"},
    ("27", "5"): {"meaning_zh": "重大的；重要的；神气活现的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("27", "6"): {"meaning_zh": "花瓶；高脚盘；夜壶", "status": "approved", "note": "llm_verified_core_meaning"},
    ("27", "7"): {"meaning_zh": "华尔兹；圆舞曲", "status": "approved", "note": "llm_verified_core_meaning"},
    ("27", "9"): {"word": "варёный", "lemma": "варёный", "meaning_zh": "煮的；熬的；炖的", "status": "approved", "note": "llm_verified_real_yo"},
    ("27", "10"): {"word": "варенье", "lemma": "варенье", "meaning_zh": "果酱；蜜饯", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("27", "11"): {"meaning_zh": "煮；做饭；用水煮；蒸煮", "status": "approved", "note": "llm_verified_core_meaning"},
    ("27", "12"): {"meaning_zh": "你们的；您的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("28", "1"): {"status": "rejected", "note": "continuation_fragment_of_vash_entry"},
    ("28", "2"): {"meaning_zh": "跑进；跑上", "status": "approved", "note": "llm_verified_core_meaning"},
    ("28", "3"): {"part_of_speech": "前", "meaning_zh": "在近处；在附近", "status": "approved", "note": "llm_corrected_pos_and_core_meaning"},
    ("28", "4"): {"meaning_zh": "向上；向上游；朝上；朝外", "status": "approved", "note": "llm_verified_core_meaning"},
    ("28", "5"): {"status": "rejected", "note": "continuation_fragment_of_vverkh_entry"},
    ("28", "6"): {"word": "вводить", "lemma": "вводить", "part_of_speech": "未", "meaning_zh": "带入；引入；输入；实行", "status": "approved", "note": "llm_recovered_headword_from_aspect_pair"},
    ("28", "7"): {"part_of_speech": "副", "meaning_zh": "在远处；离……很远", "status": "approved", "note": "llm_corrected_pos_and_core_meaning"},
    ("28", "8"): {"meaning_zh": "加倍；增加一倍；减少一半", "status": "approved", "note": "llm_verified_core_meaning"},
    ("28", "9"): {"meaning_zh": "两人；两人一起", "status": "approved", "note": "llm_verified_core_meaning"},
    ("29", "2"): {"part_of_speech": "前", "meaning_zh": "沿着；顺着；纵横；十分详尽", "status": "approved", "note": "llm_verified_core_meaning"},
    ("29", "3"): {"meaning_zh": "鼓舞；激励；使……振奋", "status": "approved", "note": "llm_verified_core_meaning"},
    ("29", "4"): {"meaning_zh": "突然；忽然；万一", "status": "approved", "note": "llm_verified_core_meaning"},
    ("29", "5"): {"meaning_zh": "桶；水桶", "status": "approved", "note": "llm_verified_core_meaning"},
    ("29", "6"): {"meaning_zh": "主要的；领先的；主持人；司仪；解说员", "status": "approved", "note": "llm_verified_core_meaning"},
    ("29", "7"): {"meaning_zh": "不是吗；因为；要知道", "status": "approved", "note": "llm_verified_core_meaning"},
    ("29", "8"): {"word": "вежливый", "lemma": "вежливый", "meaning_zh": "有礼貌的；客气的", "status": "approved", "note": "llm_corrected_ocr_headword"},
    ("29", "9"): {"word": "везде", "lemma": "везде", "meaning_zh": "到处；各处", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("29", "10"): {"meaning_zh": "运送；运输；用车船等搬运；走运", "status": "approved", "note": "llm_merged_homonymous_entry_meanings"},
    ("29", "11"): {"status": "rejected", "note": "duplicate_continuation_of_vezti_entry"},
    ("29", "12"): {"meaning_zh": "世纪；时代；一生；一辈子", "status": "approved", "note": "llm_verified_core_meaning"},
    ("30", "1"): {"status": "rejected", "note": "continuation_fragment_of_vek_entry"},
    ("30", "2"): {"status": "rejected", "note": "idiom_continuation_fragment"},
    ("30", "3"): {"meaning_zh": "命令；吩咐；嘱咐", "status": "approved", "note": "llm_verified_core_meaning"},
    ("30", "4"): {"meaning_zh": "伟大的；强大的；对……来说太大的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("30", "5"): {"word": "великолепный", "lemma": "великолепный", "meaning_zh": "富丽堂皇的；华丽的；丰盛的", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("30", "6"): {"meaning_zh": "雄伟的；宏伟的；庄严的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("30", "7"): {"meaning_zh": "大小；数量；数值；杰出人物", "status": "approved", "note": "llm_verified_core_meaning"},
    ("30", "8"): {"word": "велосипед", "lemma": "велосипед", "meaning_zh": "自行车", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("30", "9"): {"word": "веник", "lemma": "веник", "meaning_zh": "笤帚；扫帚", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("30", "10"): {"word": "вера", "lemma": "вера", "meaning_zh": "信心；信念；信仰", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("30", "11"): {"word": "верёвка", "lemma": "верёвка", "meaning_zh": "绳子；绳索", "status": "approved", "note": "llm_verified_real_yo"},
    ("30", "12"): {"word": "верить", "lemma": "верить", "meaning_zh": "相信；信任；有信心", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("31", "1"): {"status": "rejected", "note": "continuation_fragment_of_verit_entry"},
    ("31", "2"): {"meaning_zh": "正确地；忠实地；大概；想必", "status": "approved", "note": "llm_verified_core_meaning"},
    ("31", "3"): {"status": "rejected", "note": "continuation_fragment_of_verno_entry"},
    ("31", "4"): {"meaning_zh": "归还；收回；恢复", "status": "approved", "note": "llm_verified_core_meaning"},
    ("31", "5"): {"meaning_zh": "回来；返回；恢复；重新回到", "status": "approved", "note": "llm_verified_core_meaning"},
    ("31", "6"): {"word": "верный", "lemma": "верный", "meaning_zh": "忠诚的；忠实的；正确的；符合实际的", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("31", "7"): {"meaning_zh": "大概；可能地", "status": "approved", "note": "llm_verified_core_meaning"},
    ("31", "8"): {"word": "вертолёт", "lemma": "вертолёт", "meaning_zh": "直升机", "status": "approved", "note": "llm_verified_real_yo"},
    ("31", "9"): {"meaning_zh": "上部；顶部；表面；优势", "status": "approved", "note": "llm_verified_core_meaning"},
    ("31", "10"): {"word": "верхний", "lemma": "верхний", "meaning_zh": "上面的；上层的；外面的；上游的", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("31", "11"): {"meaning_zh": "顶；山顶；顶峰；荣誉的顶峰", "status": "approved", "note": "llm_verified_core_meaning"},
    ("31", "12"): {"meaning_zh": "重量；分量；影响；声望；比重", "status": "approved", "note": "llm_verified_core_meaning"},
    ("31", "13"): {"meaning_zh": "玩得痛快；尽情玩耍", "status": "approved", "note": "llm_verified_core_meaning"},
    ("32", "1"): {"status": "rejected", "note": "continuation_fragment_of_veselitsya_entry"},
    ("32", "2"): {"word": "весёлый", "lemma": "весёлый", "meaning_zh": "快乐的；愉快的；欢快的", "status": "approved", "note": "llm_verified_real_yo"},
    ("32", "3"): {"word": "весенний", "lemma": "весенний", "meaning_zh": "春天的；春季的", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("32", "4"): {"word": "весить", "lemma": "весить", "meaning_zh": "重；重量为；有分量；有价值", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("32", "5"): {"meaning_zh": "春天；春季", "status": "approved", "note": "llm_verified_core_meaning"},
    ("32", "6"): {"meaning_zh": "在春天；春季时", "status": "approved", "note": "llm_verified_core_meaning"},
    ("32", "7"): {"meaning_zh": "领；引导；驾驶；主持；进行；通往", "status": "approved", "note": "llm_verified_core_meaning"},
    ("32", "8"): {"meaning_zh": "前厅；门厅；大厅", "status": "approved", "note": "llm_verified_core_meaning"},
    ("32", "9"): {"meaning_zh": "消息；喜讯；音信", "status": "approved", "note": "llm_verified_core_meaning"},
    ("32", "10"): {"meaning_zh": "秤；磅秤；天平", "status": "approved", "note": "llm_verified_core_meaning"},
    ("32", "11"): {"meaning_zh": "整个的；全部的；一切；所有的人", "status": "approved", "note": "llm_verified_core_meaning"},
    ("32", "12"): {"word": "ветер", "lemma": "ветер", "meaning_zh": "风；风气；轻浮；头脑空虚", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("33", "1"): {"status": "rejected", "note": "continuation_fragment_of_veter_entry"},
    ("33", "2"): {"meaning_zh": "老战士；老将；老手；有经验的人", "status": "approved", "note": "llm_verified_core_meaning"},
    ("33", "3"): {"word": "ветка", "lemma": "ветка", "meaning_zh": "小树枝；（铁路的）支线", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("33", "4"): {"word": "вечер", "lemma": "вечер", "meaning_zh": "傍晚；晚上；晚会", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("33", "5"): {"word": "вечерний", "lemma": "вечерний", "meaning_zh": "傍晚的；晚间的；晚上出版或举办的", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("33", "6"): {"word": "вечером", "lemma": "вечером", "meaning_zh": "在傍晚；在晚上", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("33", "7"): {"word": "вечно", "lemma": "вечно", "meaning_zh": "永久地；永远", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("33", "8"): {"word": "вечный", "lemma": "вечный", "meaning_zh": "永恒的；永远的；经常发生的", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("33", "9"): {"word": "вешать", "lemma": "вешать", "meaning_zh": "挂；悬挂；绞死；垂下", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("33", "10"): {"meaning_zh": "物质；物体；物质成分", "status": "approved", "note": "llm_verified_core_meaning"},
    ("33", "11"): {"meaning_zh": "物品；东西；事情", "status": "approved", "note": "llm_verified_core_meaning"},
    ("33", "12"): {"status": "rejected", "note": "fixed_expression_fragment"},
    ("34", "2"): {"word": "взаимный", "lemma": "взаимный", "meaning_zh": "相互的；彼此的", "status": "approved", "note": "llm_corrected_ocr_headword"},
    ("34", "3"): {"word": "взаимоотношение", "lemma": "взаимоотношение", "meaning_zh": "相互关系；彼此关系", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("34", "4"): {"word": "взвешивать", "lemma": "взвешивать", "meaning_zh": "称量；过秤；斟酌；权衡；估量", "status": "approved", "note": "llm_corrected_stressed_e_ocr"},
    ("34", "5"): {"meaning_zh": "激动的；兴奋的", "status": "approved", "note": "llm_verified_core_meaning"},
    ("34", "6"): {"meaning_zh": "视线；目光；眼色；观点；见解", "status": "approved", "note": "llm_verified_core_meaning"},
    ("34", "7"): {"meaning_zh": "看一看；瞥一眼；望一望", "status": "approved", "note": "llm_verified_core_meaning"},
    ("34", "8"): {"meaning_zh": "深呼吸；叹气", "status": "approved", "note": "llm_verified_core_meaning"},
    ("34", "9"): {"meaning_zh": "成年的；成人的；成年人", "status": "approved", "note": "llm_verified_core_meaning"},
    ("34", "10"): {"meaning_zh": "爆炸；爆破", "status": "approved", "note": "llm_verified_core_meaning"},
    ("34", "11"): {"meaning_zh": "使爆炸；炸毁；爆破", "status": "approved", "note": "llm_verified_core_meaning"},
    ("34", "13"): {"meaning_zh": "看见；遇见；体验；感到；显然；看来", "status": "approved", "note": "llm_verified_core_meaning"},
    ("35", "1"): {"status": "rejected", "note": "continuation_fragment_of_videtsya_entry"},
    ("35", "2"): {"status": "rejected", "note": "continuation_fragment_of_videt_entry"},
    ("35", "3"): {"meaning_zh": "见面；相会；可见到；梦见；显然；大概", "status": "approved", "note": "llm_verified_core_meaning"},
    ("35", "4"): {"meaning_zh": "看得见；可以看见；显然；看来", "status": "approved", "note": "llm_verified_core_meaning"},
    ("35", "5"): {"meaning_zh": "可以看见的；著名的；重要的；杰出的；仪表堂堂的", "status": "approved", "note": "llm_verified_core_meaning"},
}


ALL_DECISIONS = {**DECISIONS, **PENDING_BATCH1_DECISIONS, **PENDING_BATCH2_DECISIONS, **PENDING_BATCH3_DECISIONS}


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply local LLM review decisions to TEM4 OCR vocabulary.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--review-only", type=Path, default=DEFAULT_REVIEW_ONLY)
    parser.add_argument("--removed", type=Path, default=DEFAULT_REMOVED)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    fieldnames = list(rows[0]) if rows else []
    counts = {"approved": 0, "rejected": 0, "needs_review": 0, "not_found": 0}
    report: list[dict[str, str]] = []
    removed_rows: list[dict[str, str]] = []
    output_rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for row in rows:
        key = ((row.get("source_page") or "").strip(), (row.get("block_index") or "").strip())
        decision = ALL_DECISIONS.get(key)
        if decision is None:
            output_rows.append(row)
            continue
        seen.add(key)
        old_word = row.get("word", "")
        old_meaning = row.get("meaning_zh", "")
        if decision.get("remove") == "true":
            counts["rejected"] += 1
            counts["removed"] = counts.get("removed", 0) + 1
            removed = dict(row)
            removed["remove_reason"] = decision.get("note", "")
            removed_rows.append(removed)
            report.append(
                {
                    "source_page": key[0],
                    "block_index": key[1],
                    "old_word": old_word,
                    "new_word": "",
                    "old_meaning_zh": old_meaning,
                    "new_meaning_zh": "",
                    "status": "removed",
                    "note": decision.get("note", ""),
                }
            )
            continue
        if decision.get("word"):
            row["word"] = decision["word"]
        if decision.get("lemma"):
            row["lemma"] = decision["lemma"]
        if decision.get("meaning_zh"):
            row["meaning_zh"] = decision["meaning_zh"]
        if decision.get("part_of_speech"):
            row["part_of_speech"] = decision["part_of_speech"]
        row["review_status"] = decision["status"]
        row["review_notes"] = ";".join(
            item for item in [row.get("review_notes", ""), "local_llm_review", decision.get("note", "")] if item
        )
        counts[decision["status"]] += 1
        report.append(
            {
                "source_page": key[0],
                "block_index": key[1],
                "old_word": old_word,
                "new_word": row.get("word", ""),
                "old_meaning_zh": old_meaning,
                "new_meaning_zh": row.get("meaning_zh", ""),
                "status": decision["status"],
                "note": decision.get("note", ""),
            }
        )
        output_rows.append(row)

    missing = sorted(set(ALL_DECISIONS) - seen)
    counts["not_found"] = len(missing)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output_rows)
    args.review_only.parent.mkdir(parents=True, exist_ok=True)
    with args.review_only.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(row for row in output_rows if row.get("review_status") == "needs_review")
    args.removed.parent.mkdir(parents=True, exist_ok=True)
    removed_fields = fieldnames + (["remove_reason"] if "remove_reason" not in fieldnames else [])
    with args.removed.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=removed_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(removed_rows)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({"counts": counts, "missing_keys": missing, "rows": report}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
