"""URI dereference được theo mẫu của DBpedia.

/resource/{tên} trả 303 tới trang HTML (/?resource={tên}) hoặc tới /data/{tên}.ttl|nt|jsonld|rdf tuỳ header
Accept; /ontology/{thuật ngữ} trả định nghĩa của lớp hoặc thuộc tính vio:.
"""

from urllib.parse import quote

from fastapi import Request
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse, Response
from rdflib import BNode, Graph
from rdflib.namespace import OWL, RDF, RDFS

from vidbpedia.common import ONTOLOGY_FILE
from vidbpedia.crawl.iri import URL_SAFE
from vidbpedia.vocab import VIO, bind_prefixes

RDF_FORMATS = {
    "ttl": ("turtle", "text/turtle"),
    "nt": ("nt", "application/n-triples"),
    "jsonld": ("json-ld", "application/ld+json"),
    "rdf": ("xml", "application/rdf+xml"),
}
ACCEPT = [
    ("text/turtle", "ttl"),
    ("application/x-turtle", "ttl"),
    ("application/n-triples", "nt"),
    ("application/ld+json", "jsonld"),
    ("application/rdf+xml", "rdf"),
]
MAX_INCOMING = 2000


def negotiate(accept):
    """Header Accept → phần mở rộng RDF; None nghĩa là trình duyệt, trả trang HTML."""
    accept = (accept or "").lower()
    return next((ext for mime, ext in ACCEPT if mime in accept), None)


def describe(graph, iri):
    """Mọi triple có iri là chủ ngữ, cùng tối đa MAX_INCOMING triple có iri là tân ngữ."""
    out = bind_prefixes(Graph())
    for p, o in graph.predicate_objects(iri):
        out.add((iri, p, o))
    for i, (s, p) in enumerate(graph.subject_predicates(iri)):
        if i >= MAX_INCOMING:
            break
        out.add((s, p, iri))
    return out


def describe_term(graph, iri):
    """Định nghĩa một thuật ngữ ontology, đủ để đọc được tiên đề.

    Mọi triple đi ra, đi tiếp qua blank node (restriction, danh sách của owl:propertyChainAxiom,
    owl:members, owl:intersectionOf); thêm lớp con, thuộc tính con, nghịch đảo trực tiếp, và các tiên đề mà
    thuật ngữ nằm trong danh sách (chuỗi thuộc tính của thuộc tính khác, nhóm rời nhau, phép giao). Chỉ lấy triple có chủ ngữ là
    thuật ngữ thì owl:propertyChainAxiom ( ... ) bị cắt thành danh sách rỗng.
    """
    out = bind_prefixes(Graph())
    seen = set()

    def walk(node):
        if node in seen:
            return
        seen.add(node)
        for p, o in graph.predicate_objects(node):
            out.add((node, p, o))
            if isinstance(o, BNode):
                walk(o)

    walk(iri)
    for s in graph.subjects(RDFS.subClassOf, iri):
        if isinstance(s, BNode):
            walk(s)  # [ a owl:Restriction ; owl:someValuesFrom ... ] rdfs:subClassOf iri
        else:
            out.add((s, RDFS.subClassOf, iri))
    for p in (RDFS.subPropertyOf, OWL.inverseOf):
        for s in graph.subjects(p, iri):
            out.add((s, p, iri))
    for cell in graph.subjects(RDF.first, iri):
        head = cell
        while (prev := graph.value(predicate=RDF.rest, object=head)) is not None:
            head = prev
        for p in (OWL.propertyChainAxiom, OWL.members, OWL.intersectionOf):
            for s in graph.subjects(p, head):
                out.add((s, p, head))
                walk(head)
                walk(s)
    return out


def add_routes(app, view):
    """Gắn route vào FastAPI; gọi trước khi mount Gradio ở '/' để không bị route của Gradio che."""

    def not_found():
        return PlainTextResponse("Không tìm thấy tài nguyên.", status_code=404)

    def page_url(iri):
        return "/?resource=" + quote(view.local(iri), safe=URL_SAFE)

    @app.get("/resource/{name:path}", include_in_schema=False)
    def resource(name: str, request: Request):
        iri = view.resolve(name)
        if iri is None:
            return not_found()
        ext = negotiate(request.headers.get("accept"))
        target = f"/data/{quote(view.local(iri), safe=URL_SAFE)}.{ext}" if ext else page_url(iri)
        return RedirectResponse(target, status_code=303, headers={"Vary": "Accept"})

    @app.get("/page/{name:path}", include_in_schema=False)
    def page(name: str):
        iri = view.resolve(name)
        return RedirectResponse(page_url(iri), status_code=303) if iri is not None else not_found()

    @app.get("/data/{name:path}", include_in_schema=False)
    def data(name: str):
        base, _, ext = name.rpartition(".")
        iri = view.resolve(base) if ext in RDF_FORMATS else None
        if iri is None:
            return not_found()
        fmt, mime = RDF_FORMATS[ext]
        body = describe(view.g, iri).serialize(format=fmt)
        return Response(
            body.encode("utf-8"),
            media_type=f"{mime}; charset=utf-8",
            headers={"Access-Control-Allow-Origin": "*"},
        )

    @app.get("/ontology.ttl", include_in_schema=False)
    def ontology_file():
        """Toàn bộ ontology vio: (file ontology/vi-ontology.ttl đã ghép từ các module)."""
        return FileResponse(
            ONTOLOGY_FILE,
            media_type="text/turtle; charset=utf-8",
            filename="vi-ontology.ttl",
            headers={"Access-Control-Allow-Origin": "*"},
        )

    @app.get("/ontology/{term}", include_in_schema=False)
    def ontology(term: str):
        iri = VIO[term]
        if next(view.g.predicate_objects(iri), None) is None:
            return PlainTextResponse("Không có thuật ngữ này trong ontology vio:.", status_code=404)
        out = describe_term(view.g, iri)
        return Response(
            out.serialize(format="turtle").encode("utf-8"),
            media_type="text/turtle; charset=utf-8",
            headers={"Access-Control-Allow-Origin": "*"},
        )

    return app
