"""Tab Cây tài nguyên: mọi tài nguyên vres: xếp theo cây lớp vio:, chỉ hiện tên.

Mỗi lớp ghi số thành viên (kể cả có lớp nhờ suy luận) và liệt kê thành viên trực tiếp, tức là không thuộc
lớp con nào, giống thư mục và tệp. Thể loại, trang đổi hướng và tài nguyên chỉ có nhãn là ba nhóm riêng.

Một lớp có thể có nhiều lớp cha (slide 03: đa kế thừa) nhưng cây chỉ vẽ được một, nên dùng một quy tắc cho
mọi lớp: cạnh của cây chỉ nối các lớp vio:, còn lớp cha dbo: ghi sau dấu "⊑" kèm nhãn DBpedia. Bốn gốc ghi
cả chuỗi lớp cha DBpedia (vio:Person ⊑ dbo:Person ⊑ dbo:Animal, theo ontology/050-dbo-alignment.ttl), để lớp
trên cùng như "Động vật" vẫn hiện ra mà không thành một nút trùng tên, trùng số với gốc vio: bên dưới.
"""

from collections import defaultdict

from rdflib.namespace import OWL, RDF, RDFS, SKOS

from vidbpedia.vocab import DBO, VIO, VRES
from vidbpedia.web.resource_page import esc, fold

ROOT_ORDER = [VIO.Person, VIO.Organisation, VIO.Location, VIO.CareerStation]
MAX_LIST = 300  # số tên tối đa mỗi nút khi không lọc
MAX_LIST_FILTERED = 100


def num(n):
    """1234 → '1.234' (dấu chấm phân cách hàng nghìn như tiếng Việt)."""
    return f"{n:,}".replace(",", ".")


class ResourceTree:
    def __init__(self, view):
        self.view = view
        g = view.g
        self.classes = sorted(
            (c for c in g.subjects(RDF.type, OWL.Class) if str(c).startswith(str(VIO))), key=str
        )
        known = set(self.classes)
        self.parent, self.dbo, self.children = {}, {}, defaultdict(list)
        for c in self.classes:
            supers = sorted(g.objects(c, RDFS.subClassOf), key=str)
            own = [s for s in supers if s in known]
            self.parent[c] = own[0] if own else None
            self.dbo[c] = [s for s in supers if str(s).startswith(str(DBO))]
            if own:
                self.children[own[0]].append(c)
        self.roots = [c for c in ROOT_ORDER if c in known and self.parent[c] is None]
        self.roots += [c for c in self.classes if self.parent[c] is None and c not in self.roots]
        # gốc không có cha vio: phía trên, nên ghi thêm tổ tiên dbo: của lớp cha dbo: đầu tiên
        self.dbo_up = {c: self._dbo_ancestors(g, self.dbo[c][0]) if self.dbo[c] else [] for c in self.roots}
        self.members = {
            c: {s for s in g.subjects(RDF.type, c) if str(s).startswith(str(VRES))} for c in self.classes
        }
        self.direct = {
            c: self.members[c] - set().union(*(self.members[d] for d in self._descendants(c)))
            for c in self.classes
        }
        self.asserted = {
            c: sum(1 for s in self.members[c] if not view.is_inferred((s, RDF.type, c))) for c in self.classes
        }
        typed = {s for s in g.subjects(RDF.type, None) if str(s).startswith(str(VRES))}
        redirects = {s for s in g.subjects(DBO.wikiPageRedirects, None) if str(s).startswith(str(VRES))}
        subjects = {s for s in g.subjects() if str(s).startswith(str(VRES))}
        self.groups = [
            (
                "skos:Concept",
                "Thể loại Wikipedia",
                "dct:subject của các thực thể",
                set(g.subjects(RDF.type, SKOS.Concept)),
            ),
            ("dbo:wikiPageRedirects", "Trang đổi hướng", "tên khác, trỏ về trang chính", redirects),
            (
                "—",
                "Tài nguyên chỉ có nhãn",
                "đích của liên kết trong infobox, chưa có lớp",
                subjects - typed - redirects,
            ),
        ]
        self._labels = {}
        self.full = self.render()

    @staticmethod
    def _dbo_ancestors(g, cls):
        """Lớp cha dbo: của cls, rồi lớp cha của lớp đó… (theo 050-dbo-alignment.ttl), dừng khi hết hoặc gặp vòng."""
        out = []
        while True:
            ups = sorted(s for s in g.objects(cls, RDFS.subClassOf) if str(s).startswith(str(DBO)))
            if not ups or ups[0] in out:
                return out
            cls = ups[0]
            out.append(cls)

    def _descendants(self, c):
        out = []
        for d in self.children[c]:
            out += [d, *self._descendants(d)]
        return out

    def label(self, s):
        if s not in self._labels:
            self._labels[s] = self.view.label(s)
        return self._labels[s]

    def dbo_link(self, d):
        """Lớp DBpedia: qname mở dbpedia.org ở tab mới, nhãn @vi (ví dụ "Động vật") hiện khi rê chuột."""
        title = f"{self.label(d)} · lớp DBpedia {d}"
        return f'<a href="{esc(str(d))}" target="_blank" rel="noopener" title="{esc(title)}">{esc(self.view.qname(d))} ↗</a>'

    def render(self, query=""):
        q = " ".join(fold(query).split())
        match = (lambda s: q in fold(self.label(s))) if q else None
        nodes = [self._class_node(c, match, depth=0) for c in self.roots]
        groups = [self._group_node(*grp, match) for grp in self.groups]
        body = "".join(n for n in nodes + groups if n)
        if not body:
            return f'<div class="rv"><p class="rv-empty">Không có tài nguyên nào có tên chứa “{esc(query)}”.</p></div>'
        roots = self.roots
        total = len({s for c in roots for s in self.members[c]}) + sum(len(grp[3]) for grp in self.groups)
        head = (
            f'<p class="ct-sum">{len(self.classes)} lớp <code>vio:</code>, lớp cha DBpedia (<code>dbo:</code>) ghi sau '
            f"dấu ⊑ · {num(total)} tài nguyên <code>vres:</code>. "
            "Số bên cạnh lớp là số thực thể của lớp và các lớp con (gồm cả thực thể có lớp nhờ suy luận); "
            "danh sách tên chỉ gồm thực thể <b>trực tiếp</b> của lớp đó.</p>"
        )
        return f'<div class="rv ct">{head}<ul class="ct-tree">{body}</ul></div>'

    def _names(self, items, match):
        items = [s for s in items if match is None or match(s)]
        cap = MAX_LIST if match is None else MAX_LIST_FILTERED
        shown = sorted(items, key=self.label)[:cap]
        lis = "".join(f"<li>{self.view.link(s, self.label(s))}</li>" for s in shown)
        rest = len(items) - len(shown)
        more = f'<p class="rv-more">… và {num(rest)} tài nguyên khác (dùng ô lọc để tìm)</p>' if rest else ""
        return (f'<ul class="ct-inst">{lis}</ul>{more}' if lis else ""), len(items)

    def _dbo_note(self, c):
        """'⊑ dbo:A, dbo:B' (lớp cha dbo: trực tiếp), với gốc thêm '⊑ dbo:X ⊑ dbo:Y' (tổ tiên), rồi nhãn DBpedia."""
        if not self.dbo[c]:
            return ""
        chain = ", ".join(self.dbo_link(d) for d in self.dbo[c])
        chain += "".join(f" ⊑ {self.dbo_link(d)}" for d in self.dbo_up.get(c, []))
        badge = '<span class="rv-badge rv-ext" title="Lớp do DBpedia định nghĩa (rdfs:isDefinedBy dbo:)">DBpedia</span>'
        return f' <span class="rv-muted">⊑ {chain}</span> {badge}'

    def _class_node(self, c, match, depth):
        kids = [self._class_node(d, match, depth + 1) for d in sorted(self.children[c], key=self.label)]
        kids = [k for k in kids if k]
        names, n_direct = self._names(self.direct[c], match)
        if match is not None and not kids and not n_direct:
            return ""
        total, asserted = len(self.members[c]), self.asserted[c]
        count = f'<span class="ct-count">{num(total)}</span>'
        if asserted == 0:
            count += ' <span class="rv-badge rv-inf">suy luận</span>'
        elif asserted < total:
            count += f' <span class="rv-muted">({num(asserted)} khai báo)</span>'
        name = f"<b>{esc(self.label(c))}</b> {self.view.link(c, self.view.qname(c))}"
        summary = f"{name}{self._dbo_note(c)} {count}"
        direct = f'<p class="ct-direct">Thực thể trực tiếp ({num(n_direct)})</p>{names}' if names else ""
        inner = (f'<ul class="ct-tree">{"".join(kids)}</ul>' if kids else "") + direct
        is_open = " open" if depth == 0 or match is not None else ""
        return f"<li><details{is_open}><summary>{summary}</summary>{inner}</details></li>"

    def _group_node(self, qname, title, note, items, match):
        names, n = self._names(items, match)
        if match is not None and not n:
            return ""
        is_open = " open" if match is not None else ""
        summary = (
            f'<b>{esc(title)}</b> <code class="rv-muted">{esc(qname)}</code> '
            f'<span class="ct-count">{num(len(items))}</span> <span class="rv-muted">{esc(note)}</span>'
        )
        return f"<li><details{is_open}><summary>{summary}</summary>{names}</details></li>"
