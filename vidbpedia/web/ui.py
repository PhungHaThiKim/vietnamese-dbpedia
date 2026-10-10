"""Giao diện Gradio, các tab theo thứ tự: Cây tài nguyên, Tài nguyên, Hỏi đáp, SPARQL."""

import json
import logging

import gradio as gr
import pandas as pd

from vidbpedia.vocab import PREFIXES
from vidbpedia.web.examples import EXAMPLE_QUERIES, EXAMPLE_QUESTIONS, RESOURCE_EXAMPLES
from vidbpedia.web.kg_rag import SparqlBasedKGRAG
from vidbpedia.web.resource_page import CLASS_NAMES
from vidbpedia.web.resource_tree import ResourceTree, num
from vidbpedia.web.theme import CSS, FORCE_LIGHT_JS, THEME

logger = logging.getLogger(__name__)

MAX_JSON_ROWS = 20  # số dòng in trong tin nhắn ở SPARQL mode; bảng bên cạnh vẫn hiện đủ
FOOTER_HTML = (
    '<div class="vd-footer"><span>Nguồn: Wikipedia tiếng Việt, Wikidata</span>'
    "<span>Semantic Web @Group 23</span></div>"
)


def header_html(stats):
    figures = [
        ("Triple", stats.get("total_triples", 0)),
        ("Thực thể", stats.get("entities", 0)),
        ("Liên kết DBpedia EN", stats.get("interlinks_to_dbpedia", 0)),
        ("Liên kết Wikidata", stats.get("interlinks_to_wikidata", 0)),
    ]
    cells = "".join(
        f'<div class="vd-stat"><span class="vd-stat-num">{num(value)}</span>'
        f'<span class="vd-stat-label">{label}</span></div>'
        for label, value in figures
    )
    parts = [f"{CLASS_NAMES.get(k, k)} {num(v)}" for k, v in stats.get("entities_by_class", {}).items() if v]
    if stats.get("inferred_triples"):
        parts.append(
            f"khai báo {num(stats['asserted_triples'])} + suy luận {num(stats['inferred_triples'])} triple"
        )
    return (
        '<header class="vd-header">'
        '<p class="vd-eyebrow">vi.dbpedia.org · Linked Open Data · SPARQL 1.1</p>'
        '<h1 class="vd-title">Vietnamese DBpedia</h1>'
        '<p class="vd-lede">Dữ liệu có cấu trúc trích từ Wikipedia tiếng Việt và Wikidata, mô tả bằng ontology '
        "<code>vio:</code> căn theo DBpedia và liên kết <code>owl:sameAs</code> sang DBpedia tiếng Anh.</p>"
        f'<div class="vd-stats">{cells}</div><p class="vd-types">{" · ".join(parts)}</p>'
        "</header>"
    )


def note(text):
    gr.Markdown(text, elem_classes=["vd-section-note"])


def tree_tab(tree):
    with gr.Tab("Cây tài nguyên", id="tree"):
        note(
            "Duyệt mọi tài nguyên `vres:` theo cây lớp `vio:`; mỗi lớp ghi lớp cha DBpedia sau dấu ⊑, gốc ghi cả chuỗi "
            "(`vio:Person ⊑ dbo:Person ⊑ dbo:Animal`). Xem chi tiết ở tab Tài nguyên."
        )
        query = gr.Textbox(label="Lọc theo tên", placeholder="ví dụ: hoàng anh, hoang anh")
        html = gr.HTML(tree.full, elem_classes=["vd-flush"])
    query.change(tree.render, query, html, trigger_mode="always_last", show_progress="hidden")


def resource_tab(view):
    with gr.Tab("Tài nguyên", id="resource"):
        note(
            "Xem một thực thể giống trang dbpedia.org/page/…: thông tin chung, liên kết dữ liệu mở, "
            "cây phân lớp, đồ thị lân cận, cây quan hệ và toàn bộ thuộc tính."
        )
        with gr.Row(equal_height=True):
            search = gr.Textbox(
                label="Tìm thực thể", placeholder="Gõ tên rồi Enter, ví dụ: cong phuong", scale=3
            )
            pick = gr.Dropdown(label="Kết quả", choices=[], scale=3)
            to_sparql = gr.Button("Mở truy vấn trong tab SPARQL", scale=1, min_width=160)
        examples = " · ".join(
            f'<a href="{view.href(view.resolve(name))}" target="_self">{label}</a>'
            for name, label in RESOURCE_EXAMPLES
            if view.resolve(name) is not None
        )
        gr.HTML(f'<p class="vd-examples">Ví dụ: {examples}</p>', elem_classes=["vd-flush"])
        html = gr.HTML(elem_classes=["vd-flush"])
        current = gr.State(None)

    def render(local, request):
        base_url = str(request.base_url).rstrip("/") if request is not None else ""
        return view.render(view.resolve(local), base_url)

    def choices(text):
        return gr.update(choices=view.search(text), value=None)

    def pick_first(text, request: gr.Request):
        results = view.search(text)
        if not results:
            empty = '<div class="rv"><p class="rv-empty">Không tìm thấy thực thể nào khớp.</p></div>'
            return gr.update(choices=[], value=None), empty, None
        local = results[0][1]
        return gr.update(choices=results, value=local), render(local, request), local

    def show(local, request: gr.Request):
        if not local:
            return gr.update(), gr.update()
        return render(local, request), local

    def on_load(request: gr.Request):
        """Mở thực thể theo ?resource= (đích của /resource/{tên} khi trình duyệt yêu cầu HTML)."""
        name = request.query_params.get("resource") if request is not None else None
        iri = view.resolve(name) if name else None
        selected = gr.Tabs(selected="resource") if iri is not None else gr.update()
        iri = iri or view.resolve(RESOURCE_EXAMPLES[0][0])
        if iri is None:
            return selected, gr.update(), "", None
        local = view.local(iri)
        return (
            selected,
            gr.update(choices=[(view.display(iri), local)], value=local),
            render(local, request),
            local,
        )

    search.change(choices, search, pick, trigger_mode="always_last", show_progress="hidden")
    search.submit(pick_first, search, [pick, html, current])
    pick.input(show, pick, [html, current])
    return {"pick": pick, "html": html, "current": current, "to_sparql": to_sparql, "on_load": on_load}


def format_sparql_mode(result):
    sparql_md = f"**Truy vấn SPARQL:**\n```sparql\n{result['sparql']}\n```"
    if result["error"]:
        return f"**Lỗi:** {result['error']}\n\n{sparql_md}"
    rows = result["rows"]
    shown = rows[:MAX_JSON_ROWS]
    count = f"{len(rows)} dòng" + (f", hiển thị {len(shown)} dòng đầu" if len(rows) > len(shown) else "")
    content = f"{sparql_md}\n\n**Kết quả** ({count}):\n```json\n{json.dumps(shown, ensure_ascii=False, indent=2)}\n```"
    if result["attempts"] > 1:
        content += f"\n\nĐã tự sửa truy vấn {result['attempts'] - 1} lần."
    return content


def format_answer(result):
    reasoning = result.get("reasoning") or "Mô hình không trả về phần suy luận."
    return f"**Trả lời:** {result['answer']}\n\n**Suy luận:**\n{reasoning}"


def chat_tab(rag):
    with gr.Tab("Hỏi đáp", id="chat"):
        note(
            "Đặt câu hỏi bằng tiếng Việt. Mô hình ngôn ngữ đọc schema của graph, viết truy vấn SPARQL, "
            "chạy trực tiếp trên dữ liệu RDF và trả lời dựa trên kết quả."
        )
        with gr.Row(equal_height=False):
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="Hội thoại", type="messages", height=500, show_copy_button=True)
                with gr.Row():
                    question = gr.Textbox(
                        show_label=False,
                        placeholder="Ví dụ: Đại học Cần Thơ được thành lập năm nào?",
                        scale=6,
                        container=False,
                    )
                    send = gr.Button("Gửi", variant="primary", scale=1, min_width=90)
                gr.Examples(examples=EXAMPLE_QUESTIONS, inputs=question, label="Câu hỏi gợi ý")
            with gr.Column(scale=2, min_width=300):
                sparql_mode = gr.Checkbox(
                    label="SPARQL mode",
                    value=False,
                    info="Hiện truy vấn SPARQL và kết quả thô, không gọi LLM viết câu trả lời",
                )
                sparql = gr.Code(label="SPARQL vừa sinh", language="sql", interactive=False, lines=8)
                with gr.Row():
                    open_in_editor = gr.Button("Mở trong tab SPARQL", size="sm")
                    clear = gr.Button("Xoá hội thoại", size="sm")
                rows = gr.Dataframe(label="Kết quả truy vấn", wrap=True, visible=False)

    def respond(message, history, sparql_only):
        history = history or []
        if not message or not message.strip():
            return history, "", gr.update(), gr.update()
        try:
            if sparql_only:
                result = rag.generate_and_run(message.strip())
                content = format_sparql_mode(result)
            else:
                result = rag.query(message.strip())
                content = format_answer(result)
        except Exception as e:  # thiếu API key, hết quota, lỗi mạng…
            logger.error("KG-RAG: %s", e)
            history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": f"**Lỗi:** {e}"},
            ]
            return history, "", "", gr.update(value=None, visible=False)
        table = pd.DataFrame(result["rows"], columns=result["columns"]) if result["rows"] else None
        history = history + [{"role": "user", "content": message}, {"role": "assistant", "content": content}]
        return history, "", result["sparql"], gr.update(value=table, visible=table is not None)

    inputs, outputs = [question, chatbot, sparql_mode], [chatbot, question, sparql, rows]
    send.click(respond, inputs, outputs)
    question.submit(respond, inputs, outputs)
    clear.click(
        lambda: ([], "", gr.update(value=None, visible=False)), None, [chatbot, sparql, rows], queue=False
    )
    return {"sparql": sparql, "open_in_editor": open_in_editor}


def sparql_tab(service):
    names = list(EXAMPLE_QUERIES)
    with gr.Tab("SPARQL", id="sparql"):
        note(
            f"Các prefix sau đã được khai báo sẵn, không cần viết lại: `{', '.join(PREFIXES)}`. "
            "Chương trình khác truy vấn cùng dữ liệu qua endpoint `/sparql` (SPARQL 1.1 Protocol) "
            "hoặc từ terminal bằng `python -m vidbpedia query`."
        )
        with gr.Row(equal_height=False):
            with gr.Column(scale=3):
                query = gr.Code(
                    label="Truy vấn",
                    language="sql",
                    lines=14,
                    interactive=True,
                    value=EXAMPLE_QUERIES[names[0]],
                )
            with gr.Column(scale=1, min_width=320):
                example = gr.Dropdown(choices=names, value=names[0], label="Truy vấn mẫu")
                output = gr.Radio(
                    choices=[("Bảng", "table"), ("JSON", "json"), ("CSV", "csv")],
                    value="table",
                    label="Định dạng kết quả",
                )
                run = gr.Button("Chạy truy vấn", variant="primary")
                clear = gr.Button("Xoá", variant="secondary")
        status = gr.Markdown(
            "Chọn truy vấn mẫu hoặc viết truy vấn, rồi bấm Chạy truy vấn.", elem_classes=["vd-status"]
        )
        table = gr.Dataframe(label="Kết quả", visible=False, wrap=True)
        text = gr.Textbox(
            label="Kết quả", lines=16, visible=False, interactive=False, elem_classes=["vd-mono"]
        )

    def execute(q, fmt):
        result, message = service.run(q, fmt)
        as_table = isinstance(result, pd.DataFrame)
        as_text = isinstance(result, str)
        return (
            gr.update(value=result if as_table else None, visible=as_table),
            gr.update(value=result if as_text else "", visible=as_text),
            message,
        )

    run.click(execute, [query, output], [table, text, status])
    clear.click(
        lambda: ("", gr.update(value=None, visible=False), gr.update(value="", visible=False), ""),
        None,
        [query, table, text, status],
    )
    example.change(lambda name: EXAMPLE_QUERIES.get(name, ""), example, query)
    output.change(lambda _: (gr.update(visible=False), gr.update(visible=False)), output, [table, text])
    return {"query": query}


def create_interface(service, view):
    rag = SparqlBasedKGRAG(service.graph)
    tree = ResourceTree(view)
    with gr.Blocks(css=CSS, title="Vietnamese DBpedia", theme=THEME, js=FORCE_LIGHT_JS) as ui:
        gr.HTML(header_html(service.stats), elem_classes=["vd-flush"])
        with gr.Tabs() as tabs:
            tree_tab(tree)
            resource = resource_tab(view)
            chat = chat_tab(rag)
            sparql = sparql_tab(service)

        def resource_query(local):
            iri = view.resolve(local)
            if iri is None:
                return gr.update(), gr.update()
            return f"SELECT ?p ?o WHERE {{\n    <{iri}> ?p ?o .\n}}\nORDER BY ?p\n", gr.Tabs(
                selected="sparql"
            )

        resource["to_sparql"].click(resource_query, resource["current"], [sparql["query"], tabs])
        chat["open_in_editor"].click(
            lambda q: (q, gr.Tabs(selected="sparql")) if q else (gr.update(), gr.update()),
            chat["sparql"],
            [sparql["query"], tabs],
        )
        gr.HTML(FOOTER_HTML, elem_classes=["vd-flush"])
        ui.load(resource["on_load"], None, [tabs, resource["pick"], resource["html"], resource["current"]])
    return ui
