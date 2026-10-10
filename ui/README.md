# ui/ — UI demo độc lập

API JSON mỏng (`ui/api`, FastAPI) + frontend Vite/React/TypeScript (`ui/web`). Không sửa `vidbpedia/`, `data/`,
`ontology/`; logic của team chỉ được import và gọi, riêng hàm private nằm trong `ui/api/adapters.py`.
Kế hoạch và quyết định: `.agents/CORE.md`, `.agents/PLAN.md`.

## Chạy

Cần Node ≥ 20.19 (khuyên dùng 22 LTS, xem `ui/web/.nvmrc`); trên Windows nếu build báo "Cannot find native binding"
thì chạy `cd ui/web && npm install --no-save @rolldown/binding-win32-x64-msvc@1.2.13` rồi build lại.

Demo (một process, nên dùng khi trình bày):
```bash
cd ui/web && npm install && npm run build
.venv/bin/python -m ui.api                      # http://127.0.0.1:8000, phục vụ cả API lẫn frontend
```
`--port` và `--host` đổi cổng/địa chỉ. Graph (~131 nghìn triple) nạp trong vài giây ở thread nền; trong lúc đó
giao diện hiện màn "Đang nạp graph…" và tự mở khi xong.

Dev (hai terminal, frontend tự reload):
```bash
.venv/bin/python -m ui.api --port 8000          # API
cd ui/web && npm run dev                        # http://localhost:5173, proxy sang :8000
API_URL=http://127.0.0.1:8010 npm run dev       # nếu API chạy ở cổng khác
```

Server Gradio của team (`python -m vidbpedia serve`, :7860) vẫn chạy độc lập.

## Các màn hình

| Route | Câu hỏi nó trả lời |
|---|---|
| `/` Tổng quan | Graph chứa gì, lớn cỡ nào, suy luận thêm được bao nhiêu? |
| `/ontology` Ontology | Cây tài nguyên như tab cùng tên của Gradio (cùng `ResourceTree`): cây lớp `vio:`, lớp cha DBpedia ghi sau dấu ⊑ kèm nhãn DBpedia (gốc ghi cả chuỗi `vio:Person ⊑ dbo:Person ⊑ dbo:Animal`, link ra dbpedia.org, rê chuột thấy nhãn tiếng Việt), số thực thể, nhãn suy luận, thực thể trực tiếp, ba nhóm Thể loại / Đổi hướng / Chỉ có nhãn, ô lọc theo tên; bên dưới là mục thu gọn "Thuộc tính và tiên đề OWL" với số triple mỗi tiên đề sinh ra; bấm mã lớp mở `/ontology/{term}` (Turtle) |
| `/entity/:id` Thực thể | X là ai, sự nghiệp (timeline) và quan hệ (đồ thị mở rộng được), nối ra LOD thế nào? |
| `/ask?q=` Hỏi đáp | Câu hỏi mẫu ở trên ô nhập; hỏi tiếng Việt thì câu trả lời cuối cùng hiện ngay dưới ô nhập, bên dưới là sáu bước tìm ra nó có thanh tiến trình (xem mục bên dưới). Ô "SPARQL mode" chỉ còn ở tab Gradio |
| `/sparql?query=` SPARQL | Soạn và chạy truy vấn, tải JSON/CSV; endpoint chuẩn cũng ở `/sparql` |
| `/map` Bản đồ | 63 tỉnh cũ / 34 tỉnh mới ghép từ graph theo `vio:successor`, tô màu theo cầu thủ/CLB/đại học, bấm tỉnh xem chi tiết |

Quy ước hiển thị xuyên suốt: **khai báo = nét liền, màu trung tính; suy luận = nét đứt, màu tím**. Công tắc
"Hiện suy luận" ở thanh trên ẩn phần suy luận ở mọi đồ thị.

## Sáu bước của màn Hỏi đáp

Mỗi bước là một thẻ đánh số; thanh tiến trình ở đầu cho biết bước nào đang chạy, xong, có cảnh báo hay bị bỏ qua,
kèm thời gian. Logic nằm ở `ui/api/linking.py` và `ui/api/qa.py`, chỉ gọi hàm công khai của `SparqlBasedKGRAG`.

| Bước | Hiện gì | Ở đâu |
|---|---|---|
| 1. Nhận diện thực thể | Cụm trong câu hỏi khớp tên nào (không cần dấu, khớp cả phần cuối tên như "quang hai"), trùng tên thì liệt kê hết | `POST /api/ask/link`, chạy vài ms nên hiện ngay |
| 2. Sinh SPARQL | Nguồn (LLM hay viết sẵn), từng lần thử: lỗi, phản hồi gửi lại LLM, lần sửa (kể cả lần "hệ thống tự sửa" không gọi LLM); truy vấn cuối; prompt đầy đủ đã gửi (schema, quy tắc, ví dụ, IRI ở bước 1) | `POST /api/ask` → `steps.generate` |
| 3. Kiểm tra truy vấn | Cú pháp, chỉ SELECT/ASK, không SERVICE/FROM, có LIMIT, IRI có thật trong graph, IRI đúng vai trò theo lớp, có dùng IRI ở bước 1, có tách thực thể trùng tên; mỗi lớp/thuộc tính `vio:`/`dbo:` trong truy vấn có bao nhiêu triple và bao nhiêu do suy luận | `steps.checks`, `steps.terms` |
| 4. Chạy trên graph | Số dòng có suy luận và chỉ khai báo, bảng kết quả có link, thời gian chạy | `rows`, `asserted`, `steps.run` |
| 5. Câu trả lời | Câu trả lời của LLM và các bước lập luận của nó (không phải suy luận OWL), đặt ở đầu kết quả ngay dưới ô nhập | `POST /api/ask/answer` |
| 6. Bằng chứng | Đồ thị các thực thể trong kết quả, cạnh suy luận nét đứt tím | `GET /api/subgraph` |

IRI tìm được ở bước 1 được chèn vào prompt ngay trước câu hỏi, nên LLM dùng thẳng `VALUES ?x { <iri> }` thay
vì đoán chuỗi `CONTAINS("…")`: câu gõ không dấu và tên trùng (hai cầu thủ Nguyễn Quang Hải) vẫn đúng. Những lỗi
kiểm tra được bằng graph không trông vào LLM (`ui/api/qa.py`):
- IRI LLM tự đặt mà graph không có, và IRI dùng sai lớp (tỉnh Huế đặt vào chỗ một trường đại học), được nêu đích
  danh trong phản hồi gửi lại LLM ở lần sửa.
- Kết quả gộp các thực thể trùng tên: hệ thống tự thêm biến thực thể vào SELECT rồi chạy lại (lần "hệ thống tự sửa").
- Bước 1 không nhận ra tên nào (ví dụ huấn luyện viên, không thuộc lớp chính của chỉ mục): prompt dặn LLM lần 1 tìm
  nhãn chứa nguyên cụm tên. Ra 0 dòng thì hệ thống tách cụm theo khoảng trắng, tự tìm thực thể có nhãn chứa đủ từng
  từ trên cả graph, và gửi cho LLM ở lần 2: IRI, lớp thật, thuộc tính nối tới nó ("kim sang sik" → `Kim_Sang-sik`,
  `vio:Person`, `?s vio:manager <…>` với `?s` là đội tuyển quốc gia).

Hỏi bằng tiếng Anh cũng được: chỉ mục tên có cả nhãn tiếng Anh ("My Dinh National Stadium", "Can Tho University"),
và câu trả lời viết theo ngôn ngữ của câu hỏi. Prompt trả lời (`adapters.ASK_ANSWER_TEMPLATE`) dặn LLM nhắc đủ mọi
dòng, không loại dòng theo hiểu biết riêng (dữ liệu đã có địa giới sau sáp nhập 2025); ghi chú về ngôn ngữ và tên
trùng nhiều thực thể đặt ở cuối prompt (`qa.answer_notes`), chỗ LLM nhỏ ít bỏ qua nhất.

Câu hỏi mẫu (`ui/api/presets.py`) mỗi câu khoe một bước và không trùng ví dụ few-shot trong prompt của team, để
demo cho thấy LLM tự viết được SPARQL cho câu mới.

## Nguồn SPARQL: LLM hay viết sẵn

`mode` của `POST /api/ask`: `"auto"` (mặc định) gọi LLM khi có `OPENAI_API_KEY`, không có key thì dùng SPARQL viết
sẵn của câu mẫu; `"llm"` luôn gọi LLM; `"cache"` chỉ dùng SPARQL viết sẵn (giao diện không dùng, để gọi API khi cần).
Ở `"auto"`, gọi LLM lỗi (mất mạng, hết quota) mà câu hỏi có SPARQL viết sẵn thì dùng bản đó và ghi lý do ở bước 2.

Gói miễn phí của nhà cung cấp chỉ có vài chục request mỗi ngày (Gemini: 20/ngày cho mỗi model) mà mỗi câu hỏi tốn 2
request, nên server nhớ kết quả LLM trong phiên: hỏi lại cùng câu không gọi lại LLM (bước 2 ghi rõ, có nút "Gọi lại
LLM", API nhận `fresh: true`). Lỗi của nhà cung cấp được đổi thành hướng dẫn ngắn (`ui/api/llm_errors.py`): hết hạn
mức (429, kèm thời gian chờ nhà cung cấp báo), sai tên model (404), key sai (401/403), không kết nối được.

SPARQL viết sẵn nằm trong `ui/api/demo_cache.json` (`origin: "manual"`) và **chạy thật** trên graph, nên kết quả
luôn đúng dữ liệu hiện tại. Câu trả lời bằng chữ khi không có key thì trống (`answer: null`); câu trả lời viết sẵn
chỉ được dùng khi SPARQL gửi lên đúng là SPARQL viết sẵn. Có key thì:
```bash
echo 'OPENAI_API_KEY=...' >> .env
.venv/bin/python -m ui.api.cache_demo            # sinh lại demo_cache.json kèm câu trả lời; kiểm tra SPARQL trước khi commit
```

## API

Tài liệu OpenAPI: `/api/docs`.

| Endpoint | Việc |
|---|---|
| `GET /api/health` | `ready`, `asserted_ready`, `llm`, tiến độ nạp |
| `GET /api/overview` | số liệu tổng quan, lớp, suy luận theo thuộc tính, thực thể nổi bật, câu hỏi mẫu và gợi ý câu gõ không dấu |
| `GET /api/tree?q=` | dữ liệu tab Cây tài nguyên: lớp `vio:` (phẳng, cha trước con; `dbo` / `dboUp` / `dboLabels` là lớp cha DBpedia, chuỗi tổ tiên của gốc và nhãn @vi), thực thể trực tiếp (300 tên, 100 khi lọc), ba nhóm còn lại; lọc không cần dấu như Gradio |
| `GET /api/ontology` | cây lớp (kèm thuộc tính có domain là lớp đó), 54 thuộc tính, tiên đề OWL (chuỗi, nghịch đảo, ràng buộc, rời nhau) và số triple suy luận của từng tiên đề |
| `GET /api/search?q=` | tìm thực thể (không cần dấu) |
| `GET /api/entity/{id}` | dữ liệu màn Thực thể |
| `GET /api/neighbors/{id}` | lân cận một bước (đồ thị) |
| `GET /api/entity/{id}/tree` | tab Cây quan hệ: cây lồng nhau tối đa 3 bước (gốc → đội → sân → tỉnh), chỉ triple khai báo (trừ `vio:playedFor`), chặng thi đấu thay bằng đội kèm ghi chú năm/trận/bàn; cùng giới hạn với trang của team |
| `GET /api/entity/{id}/graph?inferred=` | đồ thị lân cận: bố cục của trang tài nguyên Gradio (`ResourceView._graph_layout`, dùng cho đồ thị kéo thả, tên quan hệ ghi giữa mũi tên) và chính SVG tĩnh của trang đó; `inferred=false` chỉ vẽ quan hệ khai báo |
| `GET /api/subgraph?ids=a&ids=b` | cạnh giữa một tập thực thể; **lặp tham số `ids`**, không dùng dấu phẩy vì id có thể chứa `,` |
| `POST /api/ask/link`, `/api/ask`, `/api/ask/answer`, `/api/ask/asserted` | hỏi đáp theo từng bước (xem trên) |
| `GET /api/sparql/examples`, `POST /api/sparql` | SPARQL cho giao diện (`inference: false` chạy trên triple khai báo) |
| `GET/POST /sparql` | endpoint chuẩn SPARQL 1.1 Protocol, dùng lại `vidbpedia.web.endpoint` của team: JSON (mặc định), XML, CSV theo `Accept` hoặc `?format=`; CONSTRUCT trả Turtle, N-Triples, JSON-LD, RDF/XML; chặn `FROM` và `SERVICE`; `?inference=false` ngoài chuẩn |
| `GET /api/map` | điểm có toạ độ và quan hệ kế thừa |
| `GET /api/map/shapes`, `/api/map/provinces`, `/api/map/province/{id}?era=` | ranh giới 63 tỉnh (TopoJSON, gắn id), số liệu theo tỉnh, chi tiết một tỉnh |
| `GET /api/consistency/presets`, `POST /api/consistency` | thử thêm một triple rồi chạy reasoner trên graph con (không ghi graph thật) |
| `/resource/…`, `/data/…`, `/ontology/{term}`, `/ontology.ttl` | Linked Data của team, gắn nguyên vẹn; `/ontology/{term}` trả định nghĩa Turtle đầy đủ (kể cả blank node của restriction và chuỗi thuộc tính), `/ontology.ttl` trả cả ontology |

Khi graph chưa nạp xong, các đường dẫn cần graph trả 503 (`/api/health` luôn trả lời và báo tiến độ).
Trình duyệt mở `/sparql?query=…` (Accept: text/html) thấy trang SPARQL của UI; `curl` mới gọi endpoint:
```bash
curl -G localhost:8000/sparql -H 'Accept: application/sparql-results+json' --data-urlencode 'query=ASK { ?s ?p ?o }'
curl -L -H 'Accept: text/turtle' localhost:8000/resource/Đặng_Quang_Huy       # Linked Data (dereference ra Turtle)
```

## Kiểm tra
```bash
.venv/bin/python -m pytest ui/tests             # dùng dataset thật, không gọi LLM (LLM giả trong test_ask.py)
.venv/bin/ruff check ui && .venv/bin/ruff format --check ui
cd ui/web && npm run build                      # kiểm kiểu TypeScript + build
```

## Lưu ý
- rdflib không có timeout cho truy vấn: truy vấn nặng không có `LIMIT` ở trang SPARQL có thể chạy rất lâu.
- Bản đồ chạy offline: ranh giới 63 tỉnh ở `ui/api/geo/` (geoBoundaries VNM ADM1 2008, public domain, có Hoàng Sa, Trường Sa); ranh giới 34 tỉnh do frontend gộp bằng `topojson-client`.
- Graph "chỉ khai báo" (để so sánh suy luận) nạp thêm ở thread nền sau graph chính; câu hỏi đến sớm hơn sẽ thấy
  "đang nạp" rồi tự cập nhật.
- `npm audit` báo 2 lỗ hổng mức vừa ở `react-router-dom` v6 (plan chốt v6; chỉ ảnh hưởng khi triển khai công khai).
