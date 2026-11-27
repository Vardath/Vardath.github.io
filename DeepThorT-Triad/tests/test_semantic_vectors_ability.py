import json
import math
import tempfile
import unittest
from pathlib import Path
from deepthort_local.semantic_vectors import fit,eigen_symmetric,review,execute,dot
SPEC={'documents':[{'id':'car','text':'car vehicle road engine'},
                   {'id':'automobile','text':'automobile vehicle road engine'},
                   {'id':'apple','text':'apple fruit orchard harvest'},
                   {'id':'pear','text':'pear fruit orchard harvest'}],
      'query':'car','dimensions':2,'top_k':4}
class SemanticTests(unittest.TestCase):
    def test_latent_association_without_literal_overlap(self):
        r=fit(SPEC);self.assertEqual(set(r['ranked_ids'][:2]),{'car','automobile'})
        rows={v['id']:v for v in r['documents']}
        self.assertGreater(rows['automobile']['cosine_similarity'],.9)
        self.assertLess(abs(rows['apple']['cosine_similarity']),.1)
        self.assertEqual(len(r['query_vector']),2);self.assertAlmostEqual(dot(r['query_vector'],r['query_vector']),1,places=8)
        self.assertFalse(r['pretrained_embedding_model']);self.assertFalse(r['network_performed'])
        self.assertEqual(r,fit(SPEC))
    def test_real_eigenpairs_and_basis(self):
        pairs=eigen_symmetric([[2.,1.],[1.,2.]])
        self.assertAlmostEqual(pairs[0][0],3);self.assertAlmostEqual(pairs[1][0],1)
        self.assertAlmostEqual(dot(pairs[0][1],pairs[1][1]),0)
        r=fit(SPEC);self.assertAlmostEqual(dot(r['basis'][0],r['basis'][1]),0,places=8)
    def test_unknown_query_invalid_rank_and_duplicates(self):
        with self.assertRaises(ValueError):fit(dict(SPEC,query='unseenword'))
        self.assertEqual(fit(dict(SPEC,query='car unseenword'))['unknown_query_terms'],['unseenword'])
        with self.assertRaises(ValueError):fit(dict(SPEC,dimensions=4))
        bad=[dict(d) for d in SPEC['documents']];bad[1]['text']=bad[0]['text']
        with self.assertRaises(ValueError):fit(dict(SPEC,documents=bad))
    def test_guarded_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'spec.json';p.write_text(json.dumps(SPEC))
            plan,_=review(root,'spec.json','vectors.json');r=execute(root,plan)
            self.assertEqual(r['dimensions'],2);self.assertEqual(json.loads((root/'vectors.json').read_text()),fit(SPEC))
            with self.assertRaises(ValueError):execute(root,plan)
            (root/'vectors.json').unlink();p.write_text(json.dumps(dict(SPEC,query='pear')))
            with self.assertRaises(ValueError):execute(root,plan)
