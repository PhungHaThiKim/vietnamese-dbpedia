"""Test trang Ontology: /api/ontology, /ontology/{term} (đủ blank node) và /ontology.ttl."""


def test_ontology_shape(client):
    d = client.get("/api/ontology").json()
    stats = d["stats"]
    assert stats["classes"] == len(d["classes"]) == 18
    assert stats["objectProperties"] + stats["datatypeProperties"] == len(d["properties"]) == 54
    assert stats["download"] == "/ontology.ttl" and stats["triples"]

    ids = [c["id"] for c in d["classes"]]
    assert ids[0] == "vio:Person" and "vio:FootballPlayer" in ids
    player = next(c for c in d["classes"] if c["id"] == "vio:FootballPlayer")
    assert player["parent"] == "vio:Athlete" and player["dbo"] == ["dbo:SoccerPlayer"]
    assert player["depth"] == 2 and player["asserted"] == player["total"] > 0

    person = next(c for c in d["classes"] if c["id"] == "vio:Person")
    birth = next(p for p in person["properties"] if p["id"] == "vio:birthDate")
    assert birth["kind"] == "datatype" and birth["range"] == "xsd:date" and birth["functional"]
    assert "dbo:birthDate" in birth["subPropertyOf"] and birth["domain"] == "vio:Person"

    props = {p["id"]: p for p in d["properties"]}
    assert props["vio:playedFor"]["inverseOf"] == "vio:hasPlayer" and props["vio:playedFor"]["inferred"] > 0
    assert props["vio:latitude"]["domain"] is None  # cố ý không có domain (CLB, ĐH cũng có toạ độ)


def test_ontology_axioms(client):
    ax = client.get("/api/ontology").json()["axioms"]
    chain = next(a for a in ax["chains"] if a["property"] == "vio:playedFor")
    assert chain["chain"] == ["vio:careerStation", "vio:team"] and chain["inferred"] > 0
    assert any({i["a"], i["b"]} == {"vio:playedFor", "vio:hasPlayer"} for i in ax["inverses"])
    some = next(r for r in ax["restrictions"] if r["kind"] == "some")
    assert some["onClass"] == "vio:NationalTeamPlayer" and some["filler"] == "vio:NationalTeamStation"
    # dạng giao như lời giải anti-pattern Exclusivity (slide 07): FootballPlayer ⊓ ∃careerStation.NationalTeamStation
    assert some["text"] == "FootballPlayer ⊓ ∃ careerStation.NationalTeamStation ⊑ NationalTeamPlayer"
    assert some["inferred"] > 0
    assert any(r["kind"] == "all" and r["onClass"] == "vio:ClubStation" for r in ax["restrictions"])
    assert any(set(g) >= {"vio:Person", "vio:Organisation", "vio:Location"} for g in ax["disjoint"])


def test_ontology_term_includes_blank_nodes(client):
    r = client.get("/ontology/playedFor")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/turtle")
    assert "vio:careerStation" in r.text and "vio:team" in r.text  # chuỗi thuộc tính không bị cắt rỗng
    r = client.get("/ontology/ClubStation")
    assert "owl:allValuesFrom" in r.text and "owl:AllDisjointClasses" in r.text
    r = client.get("/ontology/NationalTeamPlayer")
    assert "owl:someValuesFrom" in r.text and "owl:intersectionOf" in r.text
    r = client.get("/ontology/FootballPlayer")  # lớp nằm trong phép giao của tiên đề NationalTeamPlayer
    assert "owl:intersectionOf" in r.text and "vio:NationalTeamPlayer" in r.text
    assert "rdfs:isDefinedBy" in r.text
    assert client.get("/ontology/KhongCoThuatNguNay").status_code == 404


def test_ontology_download(client):
    r = client.get("/ontology.ttl")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/turtle")
    assert "vio:playedFor" in r.text and "owl:propertyChainAxiom" in r.text
