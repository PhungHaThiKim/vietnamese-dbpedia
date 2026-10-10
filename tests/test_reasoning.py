"""Suy luận OWL-RL trên graph nhỏ: kiểu dbo:, thuộc tính dbo:, inverse, property chain, restriction; không lan owl:sameAs."""

from rdflib import Graph, Literal
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS, XSD

from vidbpedia.common import ONTOLOGY_FILE
from vidbpedia.kg.reasoning import materialize
from vidbpedia.vocab import DBO, DBR, VIO, VRES, WD

ONTOLOGY = Graph().parse(ONTOLOGY_FILE)


def small_graph():
    g = Graph()
    p, st, nt, club, tuyen = (
        VRES.Cau_thu_A,
        VRES.Cau_thu_A__1,
        VRES.Cau_thu_A__2,
        VRES.CLB_X,
        VRES.Doi_tuyen_VN,
    )
    g.add((p, RDF.type, VIO.FootballPlayer))
    g.add((p, VIO.birthDate, Literal("1997-04-12", datatype=XSD.date)))
    g.add((p, VIO.birthPlace, VRES.Ha_Noi))
    g.add((p, VIO.birthPlace, VRES.Dong_Anh))  # hai nơi sinh: không được gộp thành owl:sameAs
    g.add((p, OWL.sameAs, DBR.Player_A))
    g.add((p, OWL.sameAs, WD.Q1))
    g.add((p, VIO.careerStation, st))
    g.add((st, RDF.type, VIO.ClubStation))
    g.add((st, VIO.team, club))
    g.add((p, VIO.careerStation, nt))
    g.add((nt, RDF.type, VIO.NationalTeamStation))
    g.add((nt, VIO.team, tuyen))
    return g


def test_materialize_dbo_inverse_chain_restriction():
    inferred, errors, _ = materialize(ONTOLOGY, small_graph())
    assert errors == []
    p = VRES.Cau_thu_A
    assert (p, RDF.type, DBO.SoccerPlayer) in inferred
    assert (p, RDF.type, DBO.Person) in inferred
    assert (p, DBO.birthDate, Literal("1997-04-12", datatype=XSD.date)) in inferred
    assert (p, VIO.playedFor, VRES.CLB_X) in inferred  # property chain careerStation ∘ team
    assert (VRES.CLB_X, VIO.hasPlayer, p) in inferred  # inverse của playedFor
    assert (VRES.CLB_X, RDF.type, VIO.FootballClub) in inferred  # ClubStation ⊑ ∀team.FootballClub
    assert (VRES.CLB_X, RDF.type, DBO.SoccerClub) in inferred
    assert (p, RDF.type, VIO.NationalTeamPlayer) in inferred  # ∃careerStation.NationalTeamStation
    assert (VRES.Ha_Noi, RDF.type, VIO.Location) in inferred  # range của birthPlace


def test_national_team_player_is_intersection():
    # slide 07, anti-pattern Exclusivity: định nghĩa bằng giao FootballPlayer ⊓ ∃careerStation.NationalTeamStation
    (axiom,) = list(ONTOLOGY.subjects(RDFS.subClassOf, VIO.NationalTeamPlayer))
    members = list(Collection(ONTOLOGY, ONTOLOGY.value(axiom, OWL.intersectionOf)))
    assert members[0] == VIO.FootballPlayer
    assert ONTOLOGY.value(members[1], OWL.onProperty) == VIO.careerStation
    assert ONTOLOGY.value(members[1], OWL.someValuesFrom) == VIO.NationalTeamStation


def test_no_sameas_leak():
    inferred, _, _ = materialize(ONTOLOGY, small_graph())
    assert not list(inferred.triples((None, OWL.sameAs, None)))
    assert not any(str(s).startswith((str(DBR), str(WD))) for s in inferred.subjects())


def test_disjointness_is_reported():
    g = small_graph()
    g.add((VRES.CLB_X, RDF.type, VIO.Province))  # CLB vừa là tổ chức vừa là địa điểm
    _, errors, _ = materialize(ONTOLOGY, g)
    assert errors, "owlrl phải báo vi phạm owl:AllDisjointClasses"
