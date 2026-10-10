# Vietnamese DBpedia

Phiên bản DBpedia cho tiếng Việt về **bóng đá Việt Nam, tỉnh thành và trường đại học**. Dữ liệu có cấu trúc được
trích từ Wikipedia tiếng Việt (abstract, infobox, thể loại, redirect…) và Wikidata, mô tả bằng ontology `vio:`
căn theo DBpedia Ontology, suy luận OWL 2 RL để có thêm các triple `dbo:` như DBpedia thật, liên kết `owl:sameAs`
sang DBpedia tiếng Anh (5★), và có SPARQL endpoint chuẩn, lệnh truy vấn từ terminal, giao diện web kèm hỏi đáp bằng
ngôn ngữ tự nhiên (KG-RAG).

Đề bài: *Build a DBpedia version for Vietnamese language.*

| Yêu cầu | Thực hiện |
|---|---|
| 1. Define an ontology | `ontology/`: 18 lớp `vio:` (đều có tổ tiên `dbo:`), restriction, property chain, disjointness |
| 2. Collect Vietnamese articles | `vidbpedia/crawl/`: chọn thực thể qua Wikidata Query Service, lấy bài viết qua MediaWiki API |
| 3. Transform into 4★ (RDF) | `vidbpedia/crawl/build_rdf.py` + `vidbpedia/kg/postprocess.py` → `data/vietnamese_dbpedia.{ttl,nt}` |
| 4. Link to English DBpedia | `owl:sameAs dbr:…` qua sitelink enwiki của Wikidata (777 liên kết), mô tả bằng VoID Linkset |
| 5. SPARQL endpoint / terminal | SPARQL endpoint `/sparql` theo SPARQL 1.1 Protocol (`vidbpedia/web/endpoint.py`); lệnh `python -m vidbpedia query` (`vidbpedia/kg/query.py`); giao diện 4 tab: Cây tài nguyên, Tài nguyên (kiểu dbpedia.org/page), Hỏi đáp (LLM sinh SPARQL, có SPARQL mode), SPARQL; URI dereference được (`/resource/…`) |

## Dataset

| | |
|---|---|
| Triple | **131.543** = 88.898 khai báo + 41.730 suy luận + 859 ontology (+ VoID) |
| Thực thể | **990**: 611 cầu thủ, 61 câu lạc bộ, 10 đội tuyển quốc gia, 29 sân vận động, 168 trường đại học, 110 tỉnh (34 hiện hành + 76 đã giải thể/sáp nhập), 1 quốc gia |
| Quá trình thi đấu | 3.382 `CareerStation` của 601 cầu thủ |
| `owl:sameAs` | 777 → DBpedia EN, 990 → Wikidata |
| Làm giàu từ Wikipedia | 990 abstract, 543 ảnh, 1.154 thể loại (`dct:subject` 9.126), 1.274 redirect, 713 link ngoài |
| Infobox thô (`vip:`) | 24.605 triple, 687 thuộc tính |
| Ngôn ngữ nhãn | vi, en |
| Kiểm tra chất lượng | 0 lỗi, 0 cảnh báo (`data/validation_report.json`) |
| License | CC BY-SA 4.0 (theo Wikipedia) |

Phạm vi được chọn để graph đủ dày cho câu hỏi nhiều bước: cầu thủ → quá trình thi đấu → CLB → sân nhà → tỉnh;
cầu thủ → quê quán (tỉnh); trường đại học → tỉnh. 78% thực thể có bài tiếng Anh nên liên kết được với DBpedia.

## Kiến trúc

```
Wikidata (WDQS) ─► seeds ──► data/raw/wikidata/{seeds,facts,provinces_of,sitelinks}.json
viwiki API ─────► enrich ─► data/raw/wikipedia/pages.jsonl (+ link_targets, template_aliases)
                    │  cache HTTP: data/cache/http.sqlite (không commit), --offline để chạy lại không cần mạng
                    ▼
build (trích infobox, dựng RDF) ─► data/raw/rdf/*.ttl + mapping_stats.json
ontology ─► ontology/vi-ontology.ttl
postprocess (kiểm tra, suy luận OWL 2 RL, VoID)
    ─► data/vietnamese_dbpedia.{ttl,nt}                     bản đầy đủ, nạp vào máy chủ
    ─► data/parts/{ontology.ttl, asserted.nt, inferred.nt}  tách theo nguồn gốc
    ─► data/vietnamese_dbpedia_stats.json, data/validation_report.json
serve (FastAPI + Gradio) ─► giao diện 4 tab + SPARQL endpoint /sparql + URI dereference được /resource/…
query ─► chạy truy vấn SPARQL từ terminal (trên dataset hoặc qua --endpoint)
```

Mỗi bước là một lệnh `python -m vidbpedia <bước>`.

Chi tiết nằm trong **[ARCHITECTURE.md](ARCHITECTURE.md)**, gồm:

- Sơ đồ các tầng và luồng dữ liệu, kèm ví dụ một thực thể đi qua pipeline.
- Đồ thị RDFS/OWL: cây lớp, sơ đồ lớp, bảng 54 thuộc tính, tiên đề, quy ước IRI.
- Trích infobox theo cách của DBpedia.
- Kiểm tra chất lượng, suy luận OWL 2 RL, mô tả VoID.
- Các thành phần lúc chạy: route Linked Data, các tab giao diện, luồng KG-RAG.
- Các quyết định thiết kế, và cách thêm một lớp thực thể mới.

## Chạy

```bash
python -m venv .venv
.venv/Scripts/activate              # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                # điền key LLM nếu dùng tab Hỏi đáp

# Dữ liệu thô và dataset cuối đã có sẵn trong data/, chỉ cần chạy máy chủ:
python -m vidbpedia serve           # http://127.0.0.1:7860: giao diện, /sparql, /resource/<tên>
python -m vidbpedia query "SELECT ?s WHERE { ?s a vio:Stadium } LIMIT 5"   # truy vấn từ terminal

# Dựng lại từ đầu (lần đầu khoảng 5–8 phút; các lần sau dùng cache)
python -m vidbpedia seeds           # --offline: chỉ dùng cache, --refresh: tải lại
python -m vidbpedia enrich          # --offline, --refresh
python -m vidbpedia ontology        # ghép ontology/*.ttl → vi-ontology.ttl
python -m vidbpedia build
python -m vidbpedia postprocess --strict   # --no-reason, --reasoner rdfs, --rdfxml: xuất thêm .rdf
pytest                              # 62 test, khoảng 25 giây (thêm `pytest ui/tests` cho giao diện ui/)
```

Docker: `docker compose up --build` (cổng 7860; Virtuoso tuỳ chọn ở cổng 8890).

Đặt biến `VI_DBPEDIA_UA` để đổi User-Agent gửi tới Wikimedia (chính sách của Wikimedia yêu cầu có thông tin liên hệ).

## Giao diện

| Tab | Chức năng |
|---|---|
| **Cây tài nguyên** (mặc định) | Duyệt 8.624 tài nguyên theo cây lớp `vio:`; lớp cha DBpedia ghi sau dấu ⊑, gốc ghi cả chuỗi (`vio:Person ⊑ dbo:Person ⊑ dbo:Animal`); chỉ hiện tên, có ô lọc |
| **Tài nguyên** | Trang thực thể kiểu `dbpedia.org/page/…`: abstract, ảnh, liên kết LOD, cây phân lớp, đồ thị lân cận, cây quan hệ, bảng thuộc tính. Tìm thực thể không cần gõ dấu. |
| **Hỏi đáp** | Hỏi bằng tiếng Việt; LLM sinh SPARQL, chạy trên graph rồi trả lời; có SPARQL mode |
| **SPARQL** | Soạn và chạy truy vấn SPARQL 1.1, có 9 truy vấn mẫu, xuất bảng / JSON / CSV |

Mỗi URI `vres:` dereference được trên máy chủ: trình duyệt được chuyển tới tab Tài nguyên, còn client RDF nhận Turtle,
N-Triples, JSON-LD hoặc RDF/XML theo header `Accept`. Thuật ngữ `vio:` cũng dereference được: `/ontology/{thuật ngữ}`
trả định nghĩa Turtle đầy đủ (kể cả restriction, chuỗi thuộc tính, nhóm rời nhau), `/ontology.ttl` trả cả ontology.

```bash
curl -L -H "Accept: text/turtle" http://127.0.0.1:7860/resource/Nguyễn_Công_Phượng
curl http://127.0.0.1:7860/ontology/playedFor        # owl:propertyChainAxiom ( vio:careerStation vio:team )
curl -O http://127.0.0.1:7860/ontology.ttl
```

### Giao diện trình bày (`ui/`)

Ngoài Gradio, thư mục [`ui/`](ui/README.md) có giao diện React + API JSON mỏng chạy trên cùng dataset, dùng khi
thuyết trình: `python -m ui.api` (cổng 8000, cần build frontend một lần, Node ≥ 20.19). Các trang: **Tổng quan**
(quy mô, cây lớp, suy luận thêm được gì), **Ontology** (18 lớp, 54 thuộc tính, tiên đề OWL và số triple mỗi tiên đề
sinh ra, liên kết tới `/ontology/…`), **Thực thể** (timeline sự nghiệp, đồ thị lân cận kéo thả được, khối Linked Data với
IRI, `owl:sameAs`, tải RDF bốn định dạng; thử thêm triple sai để reasoner bắt mâu thuẫn), **Hỏi đáp có bằng chứng**,
**SPARQL** (công tắc có/không suy luận, bậc thang truy vấn mẫu) và **Bản đồ** (34 tỉnh sau sáp nhập ghép từ 63 tỉnh cũ
theo `vio:successor`, tô màu theo số cầu thủ, CLB, trường).
Mọi route Linked Data và `/sparql` của team được gắn nguyên vẹn vào máy chủ này.

## SPARQL endpoint và terminal

`/sparql` làm theo SPARQL 1.1 Protocol: nhận `GET ?query=…`, `POST` dạng form hoặc `POST` thân là truy vấn
(`application/sparql-query`). Kết quả SELECT/ASK là JSON (mặc định), XML hoặc CSV; CONSTRUCT/DESCRIBE là Turtle
(mặc định), N-Triples, JSON-LD hoặc RDF/XML, chọn theo header `Accept` hoặc tham số `format=`. 19 prefix của dự án được
khai báo sẵn. Endpoint chỉ nhận truy vấn đọc và chặn `FROM`, `SERVICE`.

```bash
curl -H "Accept: text/csv" --data-urlencode \
     "query=SELECT ?s ?cap WHERE { ?s a vio:Stadium ; vio:capacity ?cap } ORDER BY DESC(?cap) LIMIT 3" \
     http://127.0.0.1:7860/sparql

python -m vidbpedia query "ASK { vres:Nguyễn_Công_Phượng owl:sameAs dbr:Nguyễn_Công_Phượng }"
python -m vidbpedia query -f truy_van.rq --format csv          # json, xml, csv, turtle, nt, json-ld, rdf
python -m vidbpedia query --endpoint http://127.0.0.1:7860/sparql "SELECT …"   # gửi tới endpoint thay vì nạp dataset
```

Client SPARQL khác (SPARQLWrapper, YASGUI, `SPARQLStore` của rdflib) dùng được với `http://127.0.0.1:7860/sparql`.

### Cấu hình LLM cho tab Hỏi đáp

Cấu hình trong `.env`. Dùng được mọi nhà cung cấp có API tương thích OpenAI (xem `.env.example`):

| Nhà cung cấp | `OPENAI_BASE_URL` | `OPENAI_MODEL` |
|---|---|---|
| OpenAI (cần credit API, khác gói ChatGPT) | để trống | `gpt-5.5` |
| Google Gemini (gói miễn phí giới hạn 20 request/ngày với `gemini-2.5-flash`; mỗi câu hỏi tốn 2 request, SPARQL mode tốn 1) | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.5-flash` |
| Ollama (chạy trên máy) | `http://localhost:11434/v1` | `qwen2.5:7b` |

## Cấu trúc thư mục

```
vietnamese-dbpedia/
├── README.md               # tổng quan, cách chạy
├── ARCHITECTURE.md         # kiến trúc, luồng hệ thống, đồ thị RDFS/OWL
├── vidbpedia/
│   ├── __main__.py         # python -m vidbpedia <lệnh>
│   ├── common.py           # đường dẫn, logging, đọc/ghi JSON
│   ├── vocab.py            # namespace và PREFIXES
│   ├── crawl/              # thu thập và dựng RDF
│   │   ├── http.py         # cache SQLite, WDQS, MediaWiki API
│   │   ├── iri.py          # quy ước IRI vres:, dbr:, wd:
│   │   ├── wikidata_seeds.py · wiki_enrich.py
│   │   ├── infobox.py · infobox_mappings.py
│   │   └── build_rdf.py
│   ├── kg/                 # ontology, kiểm tra, suy luận, xuất dataset, truy vấn
│   │   ├── ontology.py · validation.py · reasoning.py
│   │   ├── postprocess.py
│   │   └── query.py        # python -m vidbpedia query, phần chung với /sparql
│   └── web/                # máy chủ
│       ├── app.py          # FastAPI + Gradio
│       ├── ui.py           # các tab
│       ├── theme.py · examples.py · static/ (style.css, favicon)
│       ├── sparql.py       # chạy truy vấn cho tab SPARQL
│       ├── endpoint.py     # /sparql (SPARQL 1.1 Protocol)
│       ├── resource_page.py · resource_tree.py
│       ├── linked_data.py  # /resource, /data, /ontology
│       └── kg_rag.py       # LLM sinh SPARQL và trả lời
├── ontology/               # 000-prefixes … 420-football.ttl → vi-ontology.ttl
├── data/
│   ├── raw/{wikidata,wikipedia,rdf}/      # dữ liệu thô và RDF trung gian (commit để dựng lại không cần mạng)
│   ├── parts/                             # ontology / khai báo / suy luận
│   └── vietnamese_dbpedia.{ttl,nt}, *_stats.json, validation_report.json
└── tests/
```

## Hạn chế và hướng mở rộng

- URI `vres:` mới dereference được trên máy chủ chạy `python -m vidbpedia serve` (`http://127.0.0.1:7860/resource/…`); tên miền
  `vi.dbpedia.org` không thuộc dự án nên IRI gốc chưa mở được trên Internet.
- Chưa có `dbo:wikiPageWikiLink` (toàn bộ link trong bài) và cây thể loại `skos:broader`.
- Thể loại trên Wikipedia tiếng Việt do người dùng gán nên thiếu nhất quán. Vì vậy thực thể được chọn qua Wikidata
  (`P31`, `P27`/`P17 = Q881`) thay vì duyệt cây thể loại.

## Tham khảo

- https://5stardata.info/en/
- https://www.w3.org/TR/ld-bp/ (Best Practices for Publishing Linked Data)
- https://www.w3.org/TR/void/
- https://lod-cloud.net/
- https://www.dbpedia.org/resources/sparql/
- https://mappings.dbpedia.org/server/ontology/classes/
- https://www.w3.org/TR/owl2-profiles/#OWL_2_RL
