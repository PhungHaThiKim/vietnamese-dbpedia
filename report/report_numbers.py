"""In mọi con số mà report trích dẫn, tính trực tiếp từ dataset trong data/.

    python report/report_numbers.py            # từ thư mục gốc của repo
    python report/report_numbers.py --dbpedia  # thêm kiểm tra liên kết owl:sameAs trên dbpedia.org (cần mạng)

Sửa report sau khi chạy lại pipeline: chạy script này, so với các bảng trong report/sections/.
"""

import json
import logging
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rdflib import Graph  # noqa: E402
from rdflib.namespace import OWL, RDF, RDFS  # noqa: E402

from vidbpedia.common import DATA_DIR, RAW_DIR, read_json, utf8_console  # noqa: E402
from vidbpedia.vocab import DBO, DBR, PREFIXES, VIO, VIP, VRES  # noqa: E402

logging.getLogger("rdflib.term").setLevel(logging.CRITICAL)
FULL = os.path.join(DATA_DIR, "vietnamese_dbpedia.nt")
PARTS = os.path.join(DATA_DIR, "parts")


def count(g, query):
    return int(next(iter(g.query(query, initNs=PREFIXES)))[0])


def section(title):
    print(f"\n== {title}")


def ontology_numbers(onto):
    section("Ontology (tab:ontology)")
    classes = {c for c in onto.subjects(RDF.type, OWL.Class) if str(c).startswith(str(VIO))}
    obj = {p for p in onto.subjects(RDF.type, OWL.ObjectProperty) if str(p).startswith(str(VIO))}
    dat = {p for p in onto.subjects(RDF.type, OWL.DatatypeProperty) if str(p).startswith(str(VIO))}
    func = {p for p in onto.subjects(RDF.type, OWL.FunctionalProperty) if str(p).startswith(str(VIO))}
    sub_dbo = {p for p in obj | dat if any(str(o).startswith(str(DBO)) for o in onto.objects(p, RDFS.subPropertyOf))}
    print(f"triples {len(onto)} | vio classes {len(classes)} | properties {len(obj | dat)} "
          f"(object {len(obj)}, datatype {len(dat)}) | functional {len(func)} | ⊑ dbo: {len(sub_dbo)}")
    print("disjointness axioms", len(set(onto.subjects(RDF.type, OWL.AllDisjointClasses))))


def dataset_numbers(full, asserted, inferred):
    section("Dataset (tab:dataset)")
    stats = read_json(os.path.join(DATA_DIR, "vietnamese_dbpedia_stats.json"))
    for k in ("total_triples", "asserted_triples", "inferred_triples", "ontology_triples", "entities",
              "career_stations", "interlinks_to_dbpedia", "interlinks_to_wikidata", "reasoning_seconds"):
        print(f"{k}: {stats[k]}")
    print("by class:", stats["entities_by_class"])
    print("void triples:", len(full) - stats["asserted_triples"] - stats["inferred_triples"] - stats["ontology_triples"])
    print("former provinces:", count(asserted, "SELECT (COUNT(DISTINCT ?p) AS ?n) { ?p a vio:FormerProvince }"))
    for kind in ("YouthStation", "ClubStation", "NationalTeamStation"):
        print(f"{kind}:", count(asserted, f"SELECT (COUNT(DISTINCT ?s) AS ?n) {{ ?s a vio:{kind} }}"))
    print("players with a station:", count(asserted, "SELECT (COUNT(DISTINCT ?p) AS ?n) { ?p vio:careerStation ?s }"))
    print("stations without team:", count(asserted, "SELECT (COUNT(DISTINCT ?s) AS ?n) { ?p vio:careerStation ?s FILTER NOT EXISTS { ?s vio:team ?t } }"))
    print("abstracts:", count(asserted, "SELECT (COUNT(DISTINCT ?e) AS ?n) { ?e dbo:abstract ?a }"))
    print("thumbnails:", count(asserted, "SELECT (COUNT(DISTINCT ?e) AS ?n) { ?e dbo:thumbnail ?a }"))
    print("categories:", count(asserted, "SELECT (COUNT(DISTINCT ?c) AS ?n) { ?c a skos:Concept }"),
          "| dct:subject:", count(asserted, "SELECT (COUNT(*) AS ?n) { ?e dct:subject ?c }"))
    print("redirect resources:", count(asserted, "SELECT (COUNT(DISTINCT ?r) AS ?n) { ?r dbo:wikiPageRedirects ?e }"))
    print("external links:", count(asserted, "SELECT (COUNT(*) AS ?n) { ?e dbo:wikiPageExternalLink ?l }"),
          "on", count(asserted, "SELECT (COUNT(DISTINCT ?e) AS ?n) { ?e dbo:wikiPageExternalLink ?l }"), "entities")
    print("homepages:", count(asserted, "SELECT (COUNT(DISTINCT ?e) AS ?n) { ?e foaf:homepage ?l }"))
    print("coordinates:", count(asserted, "SELECT (COUNT(DISTINCT ?e) AS ?n) { ?e vio:latitude ?l }"))
    print("english labels:", count(asserted, "SELECT (COUNT(DISTINCT ?e) AS ?n) { ?e a ?c ; rdfs:label ?l FILTER(lang(?l)='en') FILTER(STRSTARTS(STR(?c), STR(vio:))) }"))
    vip = [(s, p) for s, p, _ in asserted if str(p).startswith(str(VIP))]
    print(f"vip: triples {len(vip)}, properties {len({p for _, p in vip})}")
    vres = {s for s in asserted.subjects() if str(s).startswith(str(VRES))} | {
        o for o in asserted.objects() if str(o).startswith(str(VRES))}
    print("distinct vres: IRIs:", len(vres))
    # thực thể có nhãn nhưng không có lớp và không phải redirect / thể loại / chặng thi đấu
    print("label-only resources:", count(full, """SELECT (COUNT(DISTINCT ?x) AS ?n) {
        ?x rdfs:label ?l FILTER(STRSTARTS(STR(?x), STR(vres:)))
        FILTER NOT EXISTS { ?x a ?c } FILTER NOT EXISTS { ?x dbo:wikiPageRedirects ?y } }"""))
    sameas = Counter()
    for c in ("FootballPlayer", "FootballClub", "NationalFootballTeam", "Stadium", "University", "Province", "Country"):
        n = count(asserted, f"SELECT (COUNT(DISTINCT ?e) AS ?n) {{ ?e a vio:{c} }}")
        k = count(asserted, f"""SELECT (COUNT(DISTINCT ?e) AS ?n) {{ ?e a vio:{c} ; owl:sameAs ?d
            FILTER(STRSTARTS(STR(?d), STR(dbr:))) }}""")
        sameas[c] = (k, n)
    print("sameAs dbr by class (linked, total):", dict(sameas))


def coverage_numbers(asserted):
    section("Infobox and property coverage (tab:infobox)")
    seeds = {s["qid"]: s["cls"] for s in read_json(os.path.join(RAW_DIR, "wikidata", "seeds.json"))}
    found, total = Counter(), Counter(seeds.values())
    with open(os.path.join(RAW_DIR, "wikipedia", "pages.jsonl"), encoding="utf-8") as f:
        for r in map(json.loads, f):
            if r.get("infobox"):
                found[seeds[r["qid"]]] += 1
    print({c: f"{found[c]}/{total[c]}" for c in total})
    stats = read_json(os.path.join(RAW_DIR, "rdf", "mapping_stats.json"))
    fp = stats["football_player"]
    print("career source infobox/wikidata:", fp.get("career:infobox"), fp.get("career:wikidata"))
    targets = read_json(os.path.join(RAW_DIR, "wikipedia", "link_targets.json"))
    print("link targets:", len(targets), "| disambiguation:", sum(bool(t and t.get("disambiguation")) for t in targets.values()), "| unresolved:", sum(t is None for t in targets.values()))
    for prop in ("birthDate", "birthProvince", "height", "currentClub", "position"):
        print(f"players with vio:{prop}:", count(asserted, f"SELECT (COUNT(DISTINCT ?p) AS ?n) {{ ?p a vio:FootballPlayer ; vio:{prop} ?v }}"))
    print("universities with vio:province:", count(asserted, "SELECT (COUNT(DISTINCT ?u) AS ?n) { ?u a vio:University ; vio:province ?p }"))
    print("clubs with ground:", count(asserted, "SELECT (COUNT(DISTINCT ?c) AS ?n) { ?c a vio:FootballClub ; vio:ground ?s }"))


def reasoning_numbers(asserted_only, full, inferred):
    section("Reasoning impact (tab:reasoning)")
    rows = [
        ("dbo:Person", "SELECT (COUNT(DISTINCT ?x) AS ?n) { ?x a dbo:Person }"),
        ("dbo:SoccerPlayer", "SELECT (COUNT(DISTINCT ?x) AS ?n) { ?x a dbo:SoccerPlayer }"),
        ("dbo:Organisation", "SELECT (COUNT(DISTINCT ?x) AS ?n) { ?x a dbo:Organisation }"),
        ("dbo:Place", "SELECT (COUNT(DISTINCT ?x) AS ?n) { ?x a dbo:Place }"),
        ("vio:NationalTeamPlayer", "SELECT (COUNT(DISTINCT ?x) AS ?n) { ?x a vio:NationalTeamPlayer }"),
        ("vio:FootballClub", "SELECT (COUNT(DISTINCT ?x) AS ?n) { ?x a vio:FootballClub }"),
        ("vio:playedFor", "SELECT (COUNT(*) AS ?n) { ?x vio:playedFor ?y }"),
        ("vio:hasPlayer", "SELECT (COUNT(*) AS ?n) { ?x vio:hasPlayer ?y }"),
        ("dbo:team", "SELECT (COUNT(*) AS ?n) { ?x dbo:team ?y }"),
        ("dbo:birthPlace", "SELECT (COUNT(*) AS ?n) { ?x dbo:birthPlace ?y }"),
    ]
    for name, q in rows:
        print(f"{name}: asserted {count(asserted_only, q)} -> full {count(full, q)}")
    types = sum(1 for _ in inferred.triples((None, RDF.type, None)))
    print(f"inferred: rdf:type {types}, other {len(inferred) - types}")
    print("persons via range (not players):", count(full, """SELECT (COUNT(DISTINCT ?x) AS ?n) {
        ?x a dbo:Person FILTER NOT EXISTS { ?x a vio:FootballPlayer } }"""))


def competency_numbers(full):
    section("Competency questions (tab:cq)")
    q = {
        "current provinces": "SELECT (COUNT(DISTINCT ?p) AS ?n) { ?p a vio:Province FILTER NOT EXISTS { ?p a vio:FormerProvince } }",
        "clubs with ground in a province": "SELECT (COUNT(DISTINCT ?c) AS ?n) { ?c a vio:FootballClub ; vio:ground ?s . ?s vio:province ?p }",
        "Cong Phuong club stations": """SELECT (COUNT(DISTINCT ?st) AS ?n) { ?p rdfs:label "Nguyễn Công Phượng"@vi ; vio:careerStation ?st . ?st a vio:ClubStation }""",
        "Cong Phuong playedFor": """SELECT (COUNT(DISTINCT ?t) AS ?n) { ?p rdfs:label "Nguyễn Công Phượng"@vi ; vio:playedFor ?t }""",
        "universities in Ha Noi": """SELECT (COUNT(DISTINCT ?u) AS ?n) { ?u a vio:University ; vio:province ?h . ?h rdfs:label "Hà Nội"@vi }""",
    }
    for name, query in q.items():
        print(f"{name}: {count(full, query)}")
    top = full.query("""SELECT ?t (COUNT(DISTINCT ?p) AS ?n) { ?p a vio:FootballPlayer ; vio:birthProvince ?pr .
        ?pr rdfs:label ?t FILTER(lang(?t) = "vi") } GROUP BY ?t ORDER BY DESC(?n) LIMIT 3""", initNs=PREFIXES)
    print("top birth provinces:", [(str(t), int(n)) for t, n in top])
    clubs = full.query("""SELECT ?l (COUNT(DISTINCT ?p) AS ?n) { ?c a vio:FootballClub ; vio:hasPlayer ?p ;
        rdfs:label ?l FILTER(lang(?l) = "vi") } GROUP BY ?l ORDER BY DESC(?n) LIMIT 3""", initNs=PREFIXES)
    print("clubs with most players:", [(str(t), int(n)) for t, n in clubs])
    hn = full.query("""SELECT DISTINCT ?club WHERE {
        { SELECT DISTINCT ?p WHERE { ?p a vio:Province ; rdfs:label ?pl . FILTER(CONTAINS(LCASE(STR(?pl)), "hà nội")) } }
        ?s vio:province ?p . ?c a vio:FootballClub ; vio:ground ?s ; rdfs:label ?club . FILTER(lang(?club) = "vi") }""",
                    initNs=PREFIXES)
    print("clubs with a ground in Ha Noi:", sorted(str(r[0]) for r in hn))
    successor = full.query("""SELECT ?l ?s { ?p a vio:FormerProvince ; rdfs:label ?l ; vio:successor ?x .
        ?x rdfs:label ?s FILTER(lang(?l)='vi' && lang(?s)='vi' && STRSTARTS(STR(?l), "Hà Tây")) }""", initNs=PREFIXES)
    print("Ha Tay successor:", [(str(a), str(b)) for a, b in successor])


def dbpedia_check(asserted):
    """Liên kết owl:sameAs dbr: nào là bài viết, trang đổi hướng, hay không có trên DBpedia."""
    import requests

    section("Live DBpedia link check (tab:links)")
    owner = {str(o): s for s, o in asserted.subject_objects(OWL.sameAs)
             if str(s).startswith(str(VRES)) and str(o).startswith(str(DBR))}
    iris = sorted(owner)
    status = {}
    for i in range(0, len(iris), 80):
        values = " ".join(f"<{x}>" for x in iris[i : i + 80])
        q = f"""SELECT ?s (SAMPLE(?r) AS ?redir) WHERE {{ VALUES ?s {{ {values} }} ?s ?p ?o .
              OPTIONAL {{ ?s <http://dbpedia.org/ontology/wikiPageRedirects> ?r }} }} GROUP BY ?s"""
        r = requests.post("https://dbpedia.org/sparql", timeout=60,
                          data={"query": q, "format": "application/sparql-results+json"})
        r.raise_for_status()
        for b in r.json()["results"]["bindings"]:
            status[b["s"]["value"]] = "redirect" if "redir" in b else "article"
    c = Counter(status.get(x, "missing") for x in iris)
    print(f"links {len(iris)} | article {c['article']} | redirect {c['redirect']} | missing {c['missing']}")
    # liên kết cần sửa, kèm lớp của tài nguyên vres: trỏ tới nó
    for kind in ("redirect", "missing"):
        bad = [x for x in iris if status.get(x, "missing") == kind]
        by_cls = Counter(str(next(asserted.objects(owner[x], RDF.type), "?")).rsplit("/", 1)[-1] for x in bad)
        print(f"{kind} by class:", dict(by_cls))
        for x in bad:
            print("  ", x[len(str(DBR)):])


def main():
    utf8_console()
    onto = Graph().parse(os.path.join(PARTS, "ontology.ttl"))
    asserted = Graph().parse(os.path.join(PARTS, "asserted.nt"), format="nt")
    inferred = Graph().parse(os.path.join(PARTS, "inferred.nt"), format="nt")
    full = Graph().parse(FULL, format="nt")
    asserted_only = Graph()
    asserted_only += onto
    asserted_only += asserted
    ontology_numbers(onto)
    dataset_numbers(full, asserted, inferred)
    coverage_numbers(asserted)
    reasoning_numbers(asserted_only, full, inferred)
    competency_numbers(full)
    if "--dbpedia" in sys.argv:
        dbpedia_check(asserted)


if __name__ == "__main__":
    main()
