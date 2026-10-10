"""Test API dữ liệu (P1) trên dataset thật; không test nào gọi LLM."""

from urllib.parse import quote

from ui.api.presets import DEMO_QUESTIONS, FEATURED
from vidbpedia.common import DATASET, read_json

HUY = "Đặng_Quang_Huy"
THAN_QN = "Câu_lạc_bộ_bóng_đá_Than_Quảng_Ninh"


def url(prefix, name):
    return f"{prefix}/{quote(name)}"


def test_health(client):
    d = client.get("/api/health").json()
    assert d["ready"] is True
    assert set(d) >= {"ready", "asserted_ready", "llm", "message"}
    assert isinstance(d["llm"], bool)


def test_overview_stats_match_stats_file(client):
    stats = read_json(DATASET + "_stats.json")
    d = client.get("/api/overview").json()
    s = d["stats"]
    assert s["total"] == stats["total_triples"]
    assert s["asserted"] + s["inferred"] + s["ontology"] <= s["total"]
    assert s["entities"] == stats["entities"]
    assert s["sameAsDbpedia"] == stats["interlinks_to_dbpedia"]


def test_overview_classes_and_inference(client):
    d = client.get("/api/overview").json()
    by_class = {c["id"]: c for c in d["byClass"]}
    assert len(by_class) == 18
    person = by_class["vio:Person"]
    assert d["byClass"][0]["id"] == "vio:Person" and person["parent"] is None
    # chuỗi lớp cha DBpedia của gốc
    assert person["dbo"] == ["dbo:Person"] and person["dboUp"] == ["dbo:Animal"]
    assert by_class["vio:FootballPlayer"]["parent"] == "vio:Athlete"
    assert by_class["vio:Athlete"]["asserted"] == 0  # chỉ có nhờ suy luận
    # cha luôn đứng trước con để frontend dựng cây thụt lề chỉ bằng một lượt duyệt
    order = [c["id"] for c in d["byClass"]]
    assert all(c["parent"] is None or order.index(c["parent"]) < i for i, c in enumerate(d["byClass"]))
    inferred = {p["prop"]: p["count"] for p in d["inferredByPredicate"]}
    assert inferred["vio:playedFor"] > 0 and len(d["inferredByPredicate"]) <= 12
    assert len(d["featured"]) == len(FEATURED)  # mọi id preset đều resolve được
    assert d["questions"] == DEMO_QUESTIONS


def test_search_without_diacritics(client):
    d = client.get("/api/search", params={"q": "dang quang huy"}).json()
    assert HUY in [r["id"] for r in d]
    first = d[0]
    assert set(first) == {"id", "label", "cls", "kind"} and first["kind"] == "player"


def test_entity_career(client):
    d = client.get(url("/api/entity", HUY)).json()
    assert d["node"]["id"] == HUY and d["node"]["kind"] == "player"
    kinds = {c["kind"] for c in d["career"]}
    assert kinds == {"youth", "club", "national"}
    assert any(c["kind"] == "national" and c["start"] == 2016 for c in d["career"])
    starts = [c["start"] for c in d["career"] if c["start"] is not None]
    assert starts == sorted(starts)
    assert not any(f["prop"] == "vio:careerStation" for f in d["facts"])
    assert d["counts"]["asserted"] > 0 and d["counts"]["inferred"] > 0


def test_entity_inference_flags_and_lod(client):
    d = client.get(url("/api/entity", HUY)).json()
    facts = {f["prop"]: f for f in d["facts"]}
    assert all(v["inferred"] for v in facts["vio:playedFor"]["values"])
    assert not any(v["inferred"] for v in facts["vio:currentClub"]["values"])
    classes = {c["id"]: c for c in d["classes"]}
    assert classes["vio:FootballPlayer"]["inferred"] is False
    assert classes["vio:Athlete"]["inferred"] is True
    assert d["lod"]["dbpedia"] and d["lod"]["wikidata"] and d["lod"]["wikipedia"]
    assert d["lod"]["linkedData"].startswith("/resource/")


def test_entity_header_types_and_graph(client):
    d = client.get(url("/api/entity", "Hà_Nội")).json()
    assert d["graph"] == "http://vi.dbpedia.org"
    assert [t["id"] for t in d["types"]] == ["vio:Province"]
    assert d["types"][0]["label"] == "Tỉnh, thành phố trực thuộc trung ương"
    assert d["types"][0]["iri"] == "http://vi.dbpedia.org/ontology/Province"
    former = client.get(url("/api/entity", "Hà_Tây_(tỉnh)")).json()
    assert "vio:FormerProvince" in [t["id"] for t in former["types"]]


def test_entity_props_and_types_carry_iri_and_qname(client):
    d = client.get(url("/api/entity", "Nguyễn_Công_Phượng")).json()
    facts = {f["prop"]: f for f in d["facts"]}
    assert facts["vio:birthDate"]["iri"] == "http://vi.dbpedia.org/ontology/birthDate"
    types = {v["node"]["qname"] for v in facts["rdf:type"]["values"]}
    assert {"vio:FootballPlayer", "dbo:SoccerPlayer"} <= types
    assert all(g["iri"].startswith("http") for g in d["incoming"])


def test_entity_incoming_is_capped(client):
    d = client.get(url("/api/entity", THAN_QN)).json()
    played = next(g for g in d["incoming"] if g["prop"] == "vio:playedFor")
    assert played["count"] >= len(played["items"]) > 0
    assert all(item["inferred"] for item in played["items"])


def test_entity_not_found(client):
    r = client.get(url("/api/entity", "Không_có"))
    assert r.status_code == 404 and "Không tìm thấy" in r.json()["detail"]


def test_neighbors_show_inferred_played_for(client):
    d = client.get(url("/api/neighbors", THAN_QN), params={"limit": 24}).json()
    assert d["center"]["id"] == THAN_QN
    assert any(e["prop"] == "vio:playedFor" and e["inferred"] for e in d["edges"])
    assert d["hidden"] > 0  # CLB có hơn 24 cầu thủ nên bị cắt
    ids = {n["id"] for n in d["nodes"]}
    assert all(e["source"] in ids and e["target"] in ids for e in d["edges"])
    assert any(n["kind"] == "lod" and n.get("external") for n in d["nodes"])


def test_subgraph_between_entities(client):
    d = client.get(url("/api/entity", THAN_QN)).json()
    players = next(g for g in d["incoming"] if g["prop"] == "vio:playedFor")["items"][:10]
    ids = [THAN_QN, *(p["id"] for p in players)]
    sub = client.get("/api/subgraph", params={"ids": ids}).json()
    assert len(sub["nodes"]) == 11
    played = [e for e in sub["edges"] if e["prop"] == "vio:playedFor"]
    assert len(played) == 10 and all(e["inferred"] for e in played)
    assert not any(e["prop"] == "vio:hasPlayer" for e in sub["edges"])  # bỏ cạnh nghịch đảo song song


def test_subgraph_limit(client):
    assert client.get("/api/subgraph", params={"ids": list(map(str, range(61)))}).status_code == 422


def test_linked_data_still_works(client):
    r = client.get(url("/resource", HUY), headers={"Accept": "text/turtle"}, follow_redirects=True)
    assert r.status_code == 200 and "vres:" in r.text
    r = client.get(url("/resource", HUY), follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/?resource=")


def test_unknown_api_path_is_404(client):
    assert client.get("/api/khong-co").status_code == 404
