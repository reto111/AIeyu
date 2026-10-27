from pathlib import Path
from contextlib import closing
import hashlib,json,sqlite3,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import aspect_example_index as index
from build_aspect_example_index import replay_span

class AspectExampleIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.directory=Path(self.tmp.name)
        db=self.directory/'examples.sqlite'
        with closing(sqlite3.connect(db))as c:
            c.execute('create table examples(example_id text,source_unit text,chapter integer,book_number integer,state text,source_text text,candidate_text text,metadata_json text)')
            for identity,state,text in [('ready','original_source_ready','ловить 100%'),('candidate','model_editorial_candidate','поймать 50_'),('blocked','withheld','ловить поймать 100% 50_')]:
                meta=dict(example_id=identity,eligible_original=state=='original_source_ready',eligible_with_candidates=state!='withheld',source_text=text,candidate_text=text,source_text_sha256=hashlib.sha256(text.encode()).hexdigest(),candidate_text_sha256=hashlib.sha256(text.encode()).hexdigest())
                c.execute('insert into examples values(?,?,?,?,?,?,?,?)',(identity,identity,1,1,state,text,text,json.dumps(meta)))
            c.commit()
        (self.directory/'manifest.json').write_text(json.dumps(dict(edition='test',files={'examples.sqlite':index.fsh(db)})),'utf8')

    def test_scope_requires_explicit_candidate_and_always_rejects_withheld(self):
        self.assertEqual([x['example_id']for x in index.query(directory=self.directory)['records']],['ready'])
        self.assertEqual({x['example_id']for x in index.query(directory=self.directory,include_candidates=True)['records']},{'ready','candidate'})
        self.assertEqual(index.query(directory=self.directory,example_id='blocked',include_candidates=True)['status'],'no_evidence')

    def test_substring_is_literal_and_sql_parameters_do_not_expand_scope(self):
        self.assertEqual([x['example_id']for x in index.query(directory=self.directory,contains='%',include_candidates=True)['records']],['ready'])
        self.assertEqual([x['example_id']for x in index.query(directory=self.directory,contains='_',include_candidates=True)['records']],['candidate'])
        self.assertEqual(index.query(directory=self.directory,example_id="' OR 1=1 --",include_candidates=True)['records'],[])

    def test_export_fingerprint_detects_changed_database(self):
        with (self.directory/'examples.sqlite').open('ab')as f:f.write(b'changed')
        with self.assertRaisesRegex(ValueError,'fingerprint'):index.query(directory=self.directory)

    def test_anchor_boundary_cannot_silently_cut_an_editorial_edit(self):
        with self.assertRaisesRegex(ValueError,'boundary'):
            replay_span('abcdefgh',2,5,[dict(start=4,old='ef',new='XX')])

if __name__=='__main__':unittest.main()
