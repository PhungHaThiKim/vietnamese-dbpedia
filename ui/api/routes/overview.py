"""/api/overview: số liệu cho màn Tổng quan (quy mô, cây lớp, suy luận thêm được gì)."""

from collections import Counter

from fastapi import APIRouter

from ui.api import presets, serialize
from ui.api.state import kg

router = APIRouter(prefix="/api")

TOP_INFERRED = 12


def _stats() -> dict:
    s = kg.stats
    validation = s.get("validation", {})
    return {
        "total": s.get("total_triples"),
        "asserted": s.get("asserted_triples"),
        "inferred": s.get("inferred_triples"),
        "ontology": s.get("ontology_triples"),
        "entities": s.get("entities"),
        "careerStations": s.get("career_stations"),
        "sameAsDbpedia": s.get("interlinks_to_dbpedia"),
        "sameAsWikidata": s.get("interlinks_to_wikidata"),
        "validationErrors": validation.get("errors"),
        "validationWarnings": validation.get("warnings"),
        "built": s.get("built"),
        "reasoner": s.get("reasoner"),
        "reasoningSeconds": s.get("reasoning_seconds"),
    }


def _by_class() -> list[dict]:
    """Cây lớp vio: theo thứ tự duyệt cây (cha trước con, anh em theo nhãn), mỗi lớp một dòng phẳng; lớp cha dbo:
    ghi kèm (gốc ghi cả chuỗi, ví dụ vio:Person ⊑ dbo:Person ⊑ dbo:Animal), cùng cây với trang Ontology."""
    tree, view = kg.tree, kg.view
    out = []

    def visit(c):
        out.append(
            {
                "id": view.qname(c),
                "label": view.label(c),
                "parent": view.qname(tree.parent[c]) if tree.parent[c] is not None else None,
                **serialize.dbo_parents(tree, c),
                "total": len(tree.members[c]),
                "asserted": tree.asserted[c],
                "direct": len(tree.direct[c]),
            }
        )
        for child in sorted(tree.children[c], key=tree.label):
            visit(child)

    for r in tree.roots:
        visit(r)
    return out


def _inferred_by_predicate() -> list[dict]:
    view = kg.view
    counts = Counter(p for _, p, _ in view.inferred)
    return [
        {"prop": view.qname(p), "label": view.label(p), "count": n}
        for p, n in counts.most_common(TOP_INFERRED)
    ]


@router.get("/overview")
def overview():
    view = kg.view
    featured = [iri for iri in (view.resolve(name) for name in presets.FEATURED) if iri is not None]
    return {
        "stats": _stats(),
        "byClass": _by_class(),
        "inferredByPredicate": _inferred_by_predicate(),
        "featured": [serialize.node(view, iri) for iri in featured],
        "questions": presets.DEMO_QUESTIONS,
        "questionHint": presets.NO_DIACRITICS_EXAMPLE,
    }
