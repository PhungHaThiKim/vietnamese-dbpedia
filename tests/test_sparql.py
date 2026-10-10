"""Competency questions (Grüninger & Fox, slide 07): câu hỏi mà dataset phải trả lời được, kèm đáp án kiểm tra.

Dùng cận dưới thay cho số cứng để test không gãy khi crawl lại dữ liệu mới.

    pytest tests/test_sparql.py -v
"""

import re

from rdflib.plugins.sparql import prepareQuery

from vidbpedia.vocab import PREFIXES


def test_reasoning_gives_dbpedia_types(run):
    """Truy vấn bằng lớp dbo: ra kết quả nhờ suy luận (vio:FootballPlayer ⊑ dbo:SoccerPlayer ⊑ … ⊑ dbo:Person)."""
    rows = run("""SELECT (COUNT(DISTINCT ?f) AS ?vio) (COUNT(DISTINCT ?s) AS ?soccer) (COUNT(DISTINCT ?p) AS ?person) WHERE {
        { ?f a vio:FootballPlayer } UNION { ?s a dbo:SoccerPlayer } UNION { ?p a dbo:Person } }""")
    r = rows[0]
    assert int(r["vio"]) >= 550
    assert int(r["soccer"]) == int(r["vio"])
    assert int(r["person"]) >= int(r["vio"])


def test_career_of_cong_phuong(run):
    """Công Phượng đã thi đấu cho những CLB nào? (cầu thủ → CareerStation → đội)"""
    rows = run("""SELECT DISTINCT ?team ?start WHERE {
        { SELECT DISTINCT ?p WHERE { ?p a vio:FootballPlayer ; rdfs:label|skos:altLabel ?n .
                                     FILTER(CONTAINS(LCASE(STR(?n)), "công phượng")) } }
        ?p vio:careerStation ?st . ?st a vio:ClubStation ; vio:team ?t ; vio:startYear ?start .
        ?t rdfs:label ?team . FILTER(lang(?team) = "vi") } ORDER BY ?start""")
    teams = [str(r["team"]) for r in rows]
    assert len(teams) >= 4
    assert any("Hoàng Anh Gia Lai" in t for t in teams)


def test_inverse_and_property_chain(run):
    """HAGL vio:hasPlayer Công Phượng: suy ra từ chain careerStation∘team = playedFor và owl:inverseOf."""
    assert run("""ASK {
        ?c vio:hasPlayer ?p ; rdfs:label ?club . FILTER(CONTAINS(?club, "Hoàng Anh Gia Lai"))
        ?p rdfs:label "Nguyễn Công Phượng"@vi }""")


def test_club_ground_province_chain(run):
    """Nhiều bước: CLB → sân nhà → tỉnh."""
    rows = run(
        """SELECT (COUNT(DISTINCT ?c) AS ?n) WHERE { ?c a vio:FootballClub ; vio:ground ?s . ?s vio:province ?p }"""
    )
    assert int(rows[0]["n"]) >= 25


def test_province_with_most_players(run):
    """Tỉnh nào có nhiều cầu thủ quê quán nhất? (GROUP BY trên vio:birthProvince)"""
    rows = run("""SELECT ?t (COUNT(DISTINCT ?p) AS ?n) WHERE {
        ?p a vio:FootballPlayer ; vio:birthProvince ?pr . ?pr rdfs:label ?t . FILTER(lang(?t) = "vi")
    } GROUP BY ?t ORDER BY DESC(?n) LIMIT 5""")
    top = {str(r["t"]): int(r["n"]) for r in rows}
    assert top.get("Nghệ An", 0) >= 20


def test_universities_linked_to_provinces(run):
    """ĐH ở Hà Nội, và tỉ lệ ĐH đã nối được về tỉnh (trước đây vio:locatedIn chỉ là chuỗi tự do)."""
    rows = run("""SELECT (COUNT(DISTINCT ?u) AS ?hn) (COUNT(DISTINCT ?v) AS ?linked) (COUNT(DISTINCT ?w) AS ?all) WHERE {
        ?w a vio:University .
        OPTIONAL { ?w vio:province ?any BIND(?w AS ?v) }
        OPTIONAL { ?w vio:province ?h . ?h rdfs:label "Hà Nội"@vi BIND(?w AS ?u) } }""")
    r = rows[0]
    assert int(r["hn"]) >= 40
    assert int(r["linked"]) >= 0.7 * int(r["all"])


def test_national_team_players_by_restriction(run):
    """FootballPlayer ⊓ ∃careerStation.NationalTeamStation ⊑ NationalTeamPlayer (slide 05: restriction, slide 07: dạng giao)."""
    rows = run("SELECT (COUNT(DISTINCT ?p) AS ?n) WHERE { ?p a vio:NationalTeamPlayer }")
    assert int(rows[0]["n"]) >= 100


def test_current_and_former_provinces(run):
    """Sau đợt sắp xếp năm 2025 còn 34 tỉnh, thành phố; Hà Tây là tỉnh cũ, kế tục bởi Hà Nội."""
    rows = run(
        "SELECT (COUNT(DISTINCT ?p) AS ?n) WHERE { ?p a vio:Province . FILTER NOT EXISTS { ?p a vio:FormerProvince } }"
    )
    assert int(rows[0]["n"]) == 34
    assert run("""ASK { ?p a vio:FormerProvince ; rdfs:label ?l ; vio:successor ?s .
        FILTER(STRSTARTS(STR(?l), "Hà Tây")) ?s rdfs:label "Hà Nội"@vi }""")


def test_redirect_lookup(run):
    """Tìm theo tên khác: trang đổi hướng "Công Phượng" → "Nguyễn Công Phượng" (dbo:wikiPageRedirects)."""
    assert run(
        """ASK { ?r dbo:wikiPageRedirects ?t ; rdfs:label "Công Phượng"@vi . ?t rdfs:label "Nguyễn Công Phượng"@vi }"""
    )


def test_link_to_english_dbpedia(run):
    """owl:sameAs sang DBpedia tiếng Anh dùng IRI Unicode như DBpedia công bố."""
    assert run(
        """ASK { ?p rdfs:label "Đặng Văn Lâm"@vi ; owl:sameAs <http://dbpedia.org/resource/Đặng_Văn_Lâm> }"""
    )
    rows = run("""SELECT (COUNT(DISTINCT ?x) AS ?n) WHERE { ?x a vio:FootballClub ; owl:sameAs ?d .
        FILTER(STRSTARTS(STR(?d), "http://dbpedia.org/resource/")) }""")
    assert int(rows[0]["n"]) >= 50


def test_example_queries_run(run):
    """Mọi truy vấn mẫu của tab SPARQL biên dịch được và có kết quả."""
    from vidbpedia.web.examples import EXAMPLE_QUERIES

    for name, query in EXAMPLE_QUERIES.items():
        prepareQuery(query, initNs=PREFIXES)
        assert run(query), f"Truy vấn mẫu '{name}' không có kết quả"


def test_prompt_few_shot_examples_run(run):
    """Các ví dụ SPARQL trong prompt của tab Hỏi đáp cũng phải chạy ra kết quả trên dữ liệu thật."""
    from vidbpedia.web.kg_rag import SPARQL_GENERATION_TEMPLATE

    text = SPARQL_GENERATION_TEMPLATE.replace("{{", "{").replace("}}", "}")
    examples = re.findall(r"^# [^\n]*\n(SELECT.*?)(?=\n\n|\n\{feedback\})", text, re.S | re.M)
    assert len(examples) >= 5
    for q in examples:
        assert run(q), f"Ví dụ trong prompt không có kết quả:\n{q}"
