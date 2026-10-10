"""Tab Cây tài nguyên (vidbpedia/web/resource_tree.py): cây lớp vio: → tên thực thể, không có thuộc tính.

pytest tests/test_resource_tree.py -v
"""

import pytest

from vidbpedia.common import DATASET
from vidbpedia.vocab import DBO, VIO, VRES
from vidbpedia.web.resource_page import ResourceView
from vidbpedia.web.resource_tree import ResourceTree

CP = VRES["Nguyễn_Công_Phượng"]


@pytest.fixture(scope="module")
def tree(graph):
    return ResourceTree(ResourceView.from_files(graph, DATASET + ".nt"))


def test_class_hierarchy(tree):
    assert tree.parent[VIO.FootballPlayer] == VIO.Athlete
    assert tree.parent[VIO.Person] is None
    assert VIO.University in tree.children[VIO.EducationalInstitution]
    assert tree.roots == [VIO.Person, VIO.Organisation, VIO.Location, VIO.CareerStation]


def test_dbo_parents_are_notes_not_nodes(tree):
    # một quy tắc cho mọi lớp (slide 03: đa kế thừa, cây chỉ vẽ được một cha): cạnh của cây chỉ nối lớp vio:,
    # lớp cha dbo: ghi sau "⊑"; gốc ghi cả chuỗi lớp cha theo 050-dbo-alignment.ttl
    assert all(str(p).startswith(str(VIO)) for p in tree.parent.values() if p is not None)
    assert tree.dbo[VIO.Person] == [DBO.Person] and tree.dbo_up[VIO.Person] == [DBO.Animal]
    assert tree.dbo_up[VIO.Organisation] == [DBO.Agent] and tree.dbo_up[VIO.Location] == []
    assert tree.dbo_up[VIO.CareerStation] == [DBO.TimePeriod]
    assert tree.dbo[VIO.Athlete] == [DBO.Athlete] and VIO.Athlete not in tree.dbo_up  # không phải gốc
    html = tree.full
    # không còn nút trùng tên "Người › Người": dbo:Person, dbo:Animal chỉ là link trong dòng của vio:Person
    assert "<summary><b>Động vật</b>" not in html and html.count("<summary><b>Người</b>") == 1
    person = html[html.index("<summary><b>Người</b>") :]
    person = person[: person.index("</summary>")]
    assert person.index("dbo:Person") < person.index("dbo:Animal")
    # nhãn @vi hiện khi rê chuột
    assert 'title="Động vật · lớp DBpedia http://dbpedia.org/ontology/Animal"' in person
    # mỗi lớp có cha dbo: một nhãn "DBpedia" cho cả nhóm "⊑"
    with_dbo = sum(1 for c in tree.classes if tree.dbo[c])
    assert html.count('rv-ext" title="Lớp do DBpedia định nghĩa') == with_dbo


def test_direct_members_like_folders(tree):
    # Công Phượng từng khoác áo đội tuyển → nằm ở lớp con NationalTeamPlayer, không lặp lại ở FootballPlayer
    assert CP in tree.direct[VIO.NationalTeamPlayer]
    assert CP not in tree.direct[VIO.FootballPlayer]
    assert CP in tree.members[VIO.Person]
    players = tree.members[VIO.FootballPlayer]
    assert players == tree.direct[VIO.FootballPlayer] | tree.direct[VIO.NationalTeamPlayer]


def test_full_tree_has_names_but_no_data(tree):
    html = tree.full
    assert "vio:FootballPlayer" in html and "dbo:SoccerPlayer" in html
    assert "Nguyễn Công Phượng" in html and "/resource/" in html
    assert "Thể loại Wikipedia" in html and "Trang đổi hướng" in html
    assert "1995-01-21" not in html and "dbo:abstract" not in html  # chỉ tên, không có thuộc tính


def test_filter(tree):
    html = tree.render("cong phuong")
    assert "Nguyễn Công Phượng" in html and "Đặng Văn Lâm" not in html
    assert "Không có tài nguyên nào" in tree.render("zzzz không có")
