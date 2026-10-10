"""Test /api/tree: cùng số liệu và cùng cách lọc với tab Cây tài nguyên của Gradio (ResourceTree)."""

from ui.api.state import kg
from vidbpedia.web.resource_tree import MAX_LIST, MAX_LIST_FILTERED


def test_tree_matches_resource_tree(client):
    d = client.get("/api/tree").json()
    tree = kg.tree
    assert d["summary"]["classes"] == len(tree.classes) == 18
    assert d["summary"]["resources"] > 8000
    assert [c["id"] for c in d["classes"]][:2] == ["vio:Person", "vio:Athlete"]
    assert len(d["classes"]) == 18 and d["classes"][0]["depth"] == 0 and d["classes"][1]["depth"] == 1
    person = d["classes"][0]
    # lớp cha DBpedia ghi kèm, không thành nút; gốc có cả chuỗi và nhãn @vi để hiện khi rê chuột
    assert person["parent"] is None and person["dbo"] == ["dbo:Person"] and person["dboUp"] == ["dbo:Animal"]
    assert person["dboLabels"] == {"dbo:Person": "Người", "dbo:Animal": "Động vật"}
    athlete = d["classes"][1]
    assert athlete["dbo"] == ["dbo:Athlete"] and athlete["dboUp"] == []
    assert person["total"] == len(tree.members[_vio(tree, "Person")])
    assert person["asserted"] == 0 and person["directTotal"] == len(tree.direct[_vio(tree, "Person")])
    assert person["directShown"] == min(person["directTotal"], MAX_LIST)
    assert all({"id", "iri", "label", "kind"} <= set(i) for i in person["direct"])
    assert all(i["iri"] == "http://vi.dbpedia.org/resource/" + i["id"] for i in person["direct"])
    assert [g["title"] for g in d["groups"]] == [
        "Thể loại Wikipedia",
        "Trang đổi hướng",
        "Tài nguyên chỉ có nhãn",
    ]
    assert d["groups"][0]["total"] > 1000 and d["groups"][0]["shown"] == MAX_LIST


def test_tree_filter(client):
    d = client.get("/api/tree", params={"q": "hoang anh"}).json()  # không dấu vẫn khớp
    names = [i["label"] for c in d["classes"] for i in c["direct"]]
    assert names and all("hoàng anh" in n.lower() for n in names)
    assert all(c["directShown"] <= MAX_LIST_FILTERED for c in d["classes"])
    # chỉ còn lớp có kết quả (hoặc có con có kết quả); lớp Giai đoạn thi đấu không có tên "hoàng anh"
    ids = [c["id"] for c in d["classes"]]
    assert "vio:FootballClub" in ids
    empty = client.get("/api/tree", params={"q": "zzzz không có ai tên này"}).json()
    assert empty["classes"] == [] and empty["groups"] == []


def _vio(tree, term):
    return next(c for c in tree.classes if str(c).endswith("/" + term))
