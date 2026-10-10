"""/api/tree: dữ liệu của tab "Cây tài nguyên" (Gradio) cho trang Ontology của UI mới.

Dùng chính `ResourceTree` của team (cây lớp vio:, lớp cha dbo: ghi sau dấu ⊑, thành viên, thực thể trực tiếp, ba
nhóm Thể loại / Đổi hướng / Chỉ có nhãn) và cùng quy tắc lọc, giới hạn (300 tên mỗi nút, 100 khi lọc), nên hai giao
diện hiện cùng một con số.
"""

from fastapi import APIRouter, Query

from ui.api import serialize
from ui.api.state import kg
from vidbpedia.web.resource_page import fold
from vidbpedia.web.resource_tree import MAX_LIST, MAX_LIST_FILTERED

router = APIRouter(prefix="/api")


def _item(view, iri) -> dict:
    n = serialize.node(view, iri)
    return {"id": n["id"], "iri": n["iri"], "label": n["label"], "kind": n["kind"]}


def _names(tree, items, match):
    """→ (danh sách đã cắt, tổng số khớp); cùng cách cắt và sắp xếp với ResourceTree._names."""
    items = [s for s in items if match is None or match(s)]
    cap = MAX_LIST if match is None else MAX_LIST_FILTERED
    shown = sorted(items, key=tree.label)[:cap]
    return [_item(tree.view, s) for s in shown], len(items)


def _class_rows(tree, c, match, depth, out) -> bool:
    """Thêm lớp c và con cháu vào `out` (cha trước con); trả về False nếu đang lọc mà không có gì khớp."""
    children = sorted(tree.children[c], key=tree.label)
    direct, n_direct = _names(tree, tree.direct[c], match)
    row = {
        "id": tree.view.qname(c),
        "term": str(c).rsplit("/", 1)[-1],
        "label": tree.label(c),
        "parent": tree.view.qname(tree.parent[c]) if tree.parent[c] is not None else None,
        "depth": depth,
        **serialize.dbo_parents(tree, c),
        "total": len(tree.members[c]),
        "asserted": tree.asserted[c],
        "direct": direct,
        "directTotal": n_direct,
        "directShown": len(direct),
    }
    index = len(out)
    out.append(row)
    kept = [_class_rows(tree, d, match, depth + 1, out) for d in children]
    if match is not None and not any(kept) and not n_direct:
        del out[index:]  # lớp và cả nhánh con không có tên nào khớp: bỏ như Gradio
        return False
    return True


@router.get("/tree")
def resource_tree(q: str = Query("", max_length=200)):
    tree = kg.tree
    query = " ".join(fold(q).split())
    match = (lambda s: query in fold(tree.label(s))) if query else None

    roots = tree.roots  # 4 gốc vio:; lớp cha dbo: của gốc nằm ở dbo / dboUp, không thành nút
    classes: list[dict] = []
    for r in roots:
        _class_rows(tree, r, match, 0, classes)

    groups = []
    for qname, title, note, items in tree.groups:
        shown, n = _names(tree, items, match)
        if match is not None and not n:
            continue
        groups.append(
            {
                "id": qname,
                "title": title,
                "note": note,
                "total": len(items),
                "matched": n,
                "items": shown,
                "shown": len(shown),
            }
        )

    resources = len({s for c in roots for s in tree.members[c]}) + sum(len(grp[3]) for grp in tree.groups)
    return {
        "query": q,
        "summary": {"classes": len(tree.classes), "resources": resources},
        "classes": classes,
        "groups": groups,
    }
