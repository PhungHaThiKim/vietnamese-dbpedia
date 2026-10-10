"""Chất lượng dataset: mọi kiểm tra của validation.py ra 0 lỗi; phần suy luận không chứa owl:sameAs."""

import json
import os

from rdflib import Graph
from rdflib.namespace import OWL, RDF, RDFS

from vidbpedia.common import DATASET, PARTS_DIR
from vidbpedia.kg import validation
from vidbpedia.vocab import DBO, SCHEMA, VIO

PARTS = PARTS_DIR


def test_validation_has_no_errors():
    ontology = Graph().parse(os.path.join(PARTS, "ontology.ttl"))
    asserted = Graph().parse(os.path.join(PARTS, "asserted.nt"), format="nt")
    errors = [i for i in validation.check_asserted(ontology, asserted) if i.severity == "error"]
    assert not errors, errors[:5]


def test_tbox_lint_catches_lecture_violations():
    # lớp tên viết thường, thiếu nhãn, thiếu rdfs:isDefinedBy, không có tổ tiên dbo:; thuộc tính cha chưa khai báo kiểu
    o = Graph()
    o.add((VIO.badClass, RDF.type, OWL.Class))
    o.add((VIO.someDate, RDF.type, OWL.DatatypeProperty))
    o.add((VIO.someDate, RDFS.subPropertyOf, SCHEMA.birthDate))
    found = {(i.check, i.subject.rsplit("/", 1)[-1]) for i in validation.check_tbox(o)}
    assert {
        ("tbox-naming", "badClass"),
        ("tbox-labels", "badClass"),
        ("tbox-defined-by", "someDate"),
        ("tbox-dbo-alignment", "badClass"),
        ("tbox-untyped", "birthDate"),
    } <= found


def test_ontology_follows_lecture_conventions():
    ontology = Graph().parse(os.path.join(PARTS, "ontology.ttl"))
    assert validation.check_tbox(ontology) == []
    # lớp vio: do ontology của dự án định nghĩa; lớp dbo: mượn vẫn do DBpedia định nghĩa, nhóm chỉ thêm nhãn @vi
    assert ontology.value(VIO.Person, RDFS.isDefinedBy) == VIO[""]
    assert ontology.value(DBO.Animal, RDFS.isDefinedBy) == DBO[""]
    assert not list(ontology.triples((VIO.Animal, None, None)))  # không tạo lớp vio: trùng lớp dbo:


def test_inferred_part_has_no_sameas():
    inferred = Graph().parse(os.path.join(PARTS, "inferred.nt"), format="nt")
    assert len(inferred) > 10_000
    assert not list(inferred.triples((None, OWL.sameAs, None)))


def test_stats_report_consistent():
    with open(DATASET + "_stats.json", encoding="utf-8") as f:
        stats = json.load(f)
    assert stats["validation"]["errors"] == 0
    assert stats["entities_by_class"]["FootballPlayer"] >= 550
    assert stats["total_triples"] > stats["asserted_triples"] + stats["inferred_triples"]
    assert stats["interlinks_to_dbpedia"] >= 700
