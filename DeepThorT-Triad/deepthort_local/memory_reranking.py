"""Bounded latent reranking of already admitted historical Memory candidates.

The existing scoped shortlist and independent Memory model remain authoritative
for candidate admission and selection. No extra model call, no foreground
reranking, and no new authority. A failed or degenerate corpus preserves order.
"""
import math
from .semantic_vectors import fit

def rerank(focus,candidates):
    original=list(candidates)
    if not 4<=len(original)<=6 or not isinstance(focus,str) or not focus.strip():
        return original
    try:
        documents=[{'id':'d'+str(i),'text':item['observation']} for i,item in enumerate(original)]
        result=fit({'documents':documents,'query':focus[:600],
                    'dimensions':min(3,len(documents)-1),'top_k':len(documents)})
        scores={}
        for row in result['documents']:
            score=row['cosine_similarity']
            if score is None:continue
            if not isinstance(score,(int,float)) or isinstance(score,bool) or not math.isfinite(score) or not -1<=score<=1:
                return original
            scores[row['id']]=score
        if any('d'+str(i) not in scores for i in range(len(original))):return original
        # Preserve each same-chat / cross-project slot. Semantic ranking cannot
        # displace scoped history with foreign examples or expand the shortlist.
        groups={}
        for i,item in enumerate(original):
            groups.setdefault(item['kind'],[]).append(i)
        ranked=list(original)
        for slots in groups.values():
            ordered=sorted(slots,key=lambda i:(-scores['d'+str(i)],i))
            for destination,source in zip(slots,ordered):ranked[destination]=original[source]
        return ranked
    except (ValueError,KeyError,TypeError,ArithmeticError):
        return original
