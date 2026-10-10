"""/api/ontology: ontology vio: dạng dữ liệu thuần cho trang Ontology.

Trả cây lớp (kèm thuộc tính có domain là lớp đó), toàn bộ thuộc tính, và các tiên đề OWL (chuỗi thuộc tính,
nghịch đảo, ràng buộc, rời nhau) cùng số triple mà mỗi tiên đề sinh ra khi suy luận. Mọi thứ đọc từ chính
graph đã nạp (ontology nằm trong dataset), không đọc lại file .ttl, nên luôn khớp với dữ liệu đang phục vụ.
"""

from collections import Counter

from fastapi import APIRouter
from rdflib import URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS

from ui.api import serialize
from ui.api.state import kg
from vidbpedia.vocab import VIO

router = APIRouter(prefix="/api")


def _local(term) -> str:
    return str(term)[len(str(VIO)) :]


def _labels(g, term) -> tuple[str, str | None]:
    vi = en = None
    for label in g.objects(term, RDFS.label):
        if getattr(label, "language", None) == "vi":
            vi = str(label)
        elif getattr(label, "language", None) == "en":
            en = str(label)
    return vi or en or _local(term), en


def _qname(view, term):
    return view.qname(term) if isinstance(term, URIRef) else None


def _intersection_of(g, node):
    """→ (nút intersectionOf chứa `node`, các lớp có tên khác trong phép giao); không nằm trong phép giao → (node, [])."""
    cell = g.value(predicate=RDF.first, object=node)
    if cell is None:
        return node, []
    while (prev := g.value(predicate=RDF.rest, object=cell)) is not None:
        cell = prev
    owner = g.value(predicate=OWL.intersectionOf, object=cell)
    if owner is None:
        return node, []
    return owner, [m for m in Collection(g, cell) if isinstance(m, URIRef)]


def _properties(g, view, by_predicate: Counter) -> list[dict]:
    props = []
    for kind, cls in (("object", OWL.ObjectProperty), ("datatype", OWL.DatatypeProperty)):
        for p in g.subjects(RDF.type, cls):
            if not str(p).startswith(str(VIO)):
                continue
            vi, en = _labels(g, p)
            inverse = g.value(p, OWL.inverseOf) or g.value(predicate=OWL.inverseOf, object=p)
            props.append(
                {
                    "id": view.qname(p),
                    "term": _local(p),
                    "label": vi,
                    "labelEn": en,
                    "kind": kind,
                    "domain": _qname(view, g.value(p, RDFS.domain)),
                    "range": _qname(view, g.value(p, RDFS.range)),
                    "subPropertyOf": sorted(
                        view.qname(s) for s in g.objects(p, RDFS.subPropertyOf) if isinstance(s, URIRef)
                    ),
                    "functional": (p, RDF.type, OWL.FunctionalProperty) in g,
                    "inverseOf": _qname(view, inverse),
                    "inferred": by_predicate.get(p, 0),
                }
            )
    props.sort(key=lambda d: (d["kind"] != "object", d["id"]))
    return props


def _classes(g, view, tree, props: list[dict]) -> list[dict]:
    """Phẳng, cha trước con (như /api/overview), kèm độ sâu và thuộc tính có domain là lớp đó."""
    by_domain: dict[str, list[dict]] = {}
    for p in props:
        if p["domain"]:
            by_domain.setdefault(p["domain"], []).append(p)
    out = []

    def visit(c, depth):
        qname = view.qname(c)
        vi, en = _labels(g, c)
        out.append(
            {
                "id": qname,
                "term": _local(c),
                "label": vi,
                "labelEn": en,
                "parent": view.qname(tree.parent[c]) if tree.parent[c] is not None else None,
                **serialize.dbo_parents(tree, c),
                "depth": depth,
                "asserted": tree.asserted[c],
                "total": len(tree.members[c]),
                "properties": by_domain.get(qname, []),
            }
        )
        for child in sorted(tree.children[c], key=tree.label):
            visit(child, depth + 1)

    for r in tree.roots:
        visit(r, 0)
    return out


def _axioms(g, view, by_predicate: Counter, by_type: Counter) -> dict:
    chains = []
    for p, head in g.subject_objects(OWL.propertyChainAxiom):
        chains.append(
            {
                "property": view.qname(p),
                "chain": [view.qname(x) for x in Collection(g, head)],
                "inferred": by_predicate.get(p, 0),
            }
        )

    inverses, seen = [], set()
    for a, b in g.subject_objects(OWL.inverseOf):
        key = frozenset((a, b))
        if key in seen:
            continue
        seen.add(key)
        inverses.append(
            {
                "a": view.qname(a),
                "b": view.qname(b),
                "inferredA": by_predicate.get(a, 0),
                "inferredB": by_predicate.get(b, 0),
            }
        )

    restrictions = []
    for r in g.subjects(RDF.type, OWL.Restriction):
        prop = g.value(r, OWL.onProperty)
        some, every = g.value(r, OWL.someValuesFrom), g.value(r, OWL.allValuesFrom)
        if prop is None or (some is None and every is None):
            continue
        if some is not None:
            # [restriction] rdfs:subClassOf C  ⇔  ∃ p.F ⊑ C : thực thể có p tới một F được gán lớp C.
            # Restriction nằm trong một phép giao (A ⊓ ∃ p.F ⊑ C, lời giải anti-pattern Exclusivity) thì
            # tiên đề nằm trên nút intersectionOf và các lớp A đứng trước.
            head, others = _intersection_of(g, r)
            on_class, filler, kind = g.value(head, RDFS.subClassOf), some, "some"
            lhs = " ⊓ ".join([*(_local(a) for a in others), f"∃ {_local(prop)}.{_local(filler)}"])
            text = f"{lhs} ⊑ {_local(on_class)}" if on_class is not None else ""
            inferred = by_type.get(on_class, 0)
        else:
            # C rdfs:subClassOf [restriction]  ⇔  C ⊑ ∀ p.F : mọi giá trị p của một C được gán lớp F
            on_class, filler, kind = g.value(predicate=RDFS.subClassOf, object=r), every, "all"
            text = f"{_local(on_class)} ⊑ ∀ {_local(prop)}.{_local(filler)}" if on_class is not None else ""
            inferred = by_type.get(filler, 0)
        restrictions.append(
            {
                "kind": kind,
                "onClass": _qname(view, on_class),
                "property": view.qname(prop),
                "filler": _qname(view, filler),
                "text": text,
                "inferred": inferred,
            }
        )
    restrictions.sort(key=lambda d: (d["kind"] != "some", d["text"]))

    disjoint = []
    for axiom in g.subjects(RDF.type, OWL.AllDisjointClasses):
        head = g.value(axiom, OWL.members)
        if head is not None:
            disjoint.append([view.qname(x) for x in Collection(g, head)])
    disjoint.sort(key=lambda group: (-len(group), group))

    chains.sort(key=lambda d: d["property"])
    inverses.sort(key=lambda d: d["a"])
    return {"chains": chains, "inverses": inverses, "restrictions": restrictions, "disjoint": disjoint}


@router.get("/ontology")
def ontology():
    g, view, tree = kg.graph, kg.view, kg.tree
    by_predicate = Counter(p for _, p, _ in view.inferred)
    by_type = Counter(o for _, p, o in view.inferred if p == RDF.type)
    props = _properties(g, view, by_predicate)
    classes = _classes(g, view, tree, props)
    return {
        "stats": {
            "classes": len(classes),
            "objectProperties": sum(1 for p in props if p["kind"] == "object"),
            "datatypeProperties": sum(1 for p in props if p["kind"] == "datatype"),
            "triples": kg.stats.get("ontology_triples"),
            "download": "/ontology.ttl",
            "namespace": str(VIO),
        },
        "classes": classes,
        "properties": props,
        "axioms": _axioms(g, view, by_predicate, by_type),
    }
