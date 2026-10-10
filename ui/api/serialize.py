"""Đổi term rdflib thành JSON thuần: node, giá trị, cạnh. Dùng chung cho mọi route.

Quy ước (xem .agents/PLAN.md §2.2): id thực thể = local name trong vres:, IRI khác dùng nguyên IRI làm id.
`inferred` đánh dấu triple có trong `view.inferred`; đây là thông tin quan trọng nhất của UI.
"""

import re

from rdflib import Literal, URIRef

from vidbpedia.vocab import PREFIXES, VRES

# vres:/vcat: là thực thể; dbr:/wd: là LOD bên ngoài; phần còn lại là thuật ngữ schema (vio:, dbo:, rdf:…)
_SCHEMA_NS = tuple(ns for p, ns in PREFIXES.items() if p not in ("vres", "vcat", "dbr", "wd"))
_YEAR = re.compile(r"-?\d+")


def node_id(view, iri) -> str:
    s = str(iri)
    return view.local(iri) if s.startswith(str(VRES)) else s


def node(view, iri) -> dict:
    """{id, iri, label, cls, kind, external?}. IRI không thuộc vres: có `external: true`."""
    s = str(iri)
    if s.startswith(str(VRES)):
        return {
            "id": view.local(iri),
            "iri": s,
            "label": view.label(iri),
            "cls": view.class_name(iri),
            "kind": view.kind(iri),
        }
    kind = "other" if s.startswith(_SCHEMA_NS) else "lod"
    return {
        "id": s,
        "iri": s,
        "qname": view.qname(iri),
        "label": view.label(iri),
        "cls": "",
        "kind": kind,
        "external": True,
    }


def value(view, s, p, o) -> dict:
    """Giá trị của triple (s, p, o): literal hoặc IRI, kèm cờ suy luận."""
    inferred = (s, p, o) in view.inferred
    if isinstance(o, URIRef):
        return {"type": "iri", "node": node(view, o), "inferred": inferred}
    out = {"type": "literal", "value": str(o), "inferred": inferred}
    if isinstance(o, Literal):
        if o.language:
            out["lang"] = o.language
        if o.datatype is not None:
            out["datatype"] = view.qname(o.datatype)
    return out


def edge(view, s, p, o) -> dict:
    return {
        "source": node_id(view, s),
        "target": node_id(view, o),
        "prop": view.qname(p),
        "propLabel": view.label(p),
        "inferred": (s, p, o) in view.inferred,
    }


def year(term) -> int | None:
    """xsd:gYear → int; dataset có cả năm âm (trước Công nguyên); không đọc được thì None."""
    m = _YEAR.match(str(term)) if term is not None else None
    return int(m.group()) if m else None


def integer(term) -> int | None:
    try:
        return int(str(term))
    except (TypeError, ValueError):
        return None


def dbo_parents(tree, c) -> dict:
    """Lớp cha DBpedia của lớp vio: c, ghi sau dấu ⊑ trên cây: {dbo: cha trực tiếp, dboUp: tổ tiên (chỉ với gốc),
    dboLabels: qname → nhãn @vi để hiện khi rê chuột, ví dụ dbo:Animal → "Động vật"}."""
    q = tree.view.qname
    up = tree.dbo_up.get(c, [])
    return {
        "dbo": [q(d) for d in tree.dbo[c]],
        "dboUp": [q(d) for d in up],
        "dboLabels": {q(d): tree.label(d) for d in [*tree.dbo[c], *up]},
    }
