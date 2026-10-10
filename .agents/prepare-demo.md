# Chuẩn bị thuyết trình demo UI

> Mục tiêu: trả lời được mọi câu "cái này trên màn hình lấy từ đâu trên graph, vì sao đúng?".
> Thầy hiếm khi hỏi React/CSS; thầy chỉ vào UI và hỏi về triple, ontology, suy luận.

## 1. Năm mảng cần nắm

| # | Mảng | Vì sao cần | Ưu tiên |
|---|---|---|---|
| 1 | Ontology & suy luận | Trọng tâm môn học, bị hỏi nhiều nhất; UI tách khai báo/suy luận nên thầy thấy ngay | 1 |
| 2 | Linked Data & SPARQL | Yêu cầu đề 4–5: `owl:sameAs` sang DBpedia, URI dereference, endpoint chuẩn, Hỏi đáp sinh SPARQL | 2 |
| 3 | Các màn UI | Mỗi màn phải nói được "chứng minh yêu cầu đề nào" | 3 |
| 4 | Domain bài toán | Vì sao bóng đá + tỉnh + đại học: thực thể trỏ lẫn nhau (cầu thủ → đội → sân → tỉnh) | 4 |
| 5 | Luồng dữ liệu | "Dữ liệu ở đâu ra, sao tin được?" — chỉ cần mức sơ đồ, không cần code crawl | 5 |

Mẹo: học cả 5 mảng qua **một thực thể xuyên suốt — Đặng Quang Huy** (domain, ontology, suy luận, sameAs, SPARQL).

## 2. Kiến thức nền

| Chủ đề | Mức cần nắm |
|---|---|
| RDF | Triple, IRI, literal có kiểu (`xsd:gYear`) / có ngôn ngữ (`@vi`); đọc được Turtle, N-Triples |
| RDFS | `subClassOf`, `subPropertyOf`, `domain`, `range`. **Bẫy:** `range` là luật suy luận, không phải ràng buộc (48 HLV/chủ tịch/hiệu trưởng thành `dbo:Person` nhờ `rdfs:range`) |
| OWL | `inverseOf`, `propertyChainAxiom`, `someValuesFrom`/`allValuesFrom`, `AllDisjointClasses`, `sameAs`; OWL 2 RL là gì (luật if-then, forward chaining) |
| Giả định thế giới mở | Thiếu triple ≠ sai → restriction OWL dùng để *suy ra*, không để *kiểm tra* |
| SPARQL | SELECT, OPTIONAL, FILTER, FILTER NOT EXISTS, subquery, COUNT/GROUP BY |
| Linked Data | 4 nguyên tắc Berners-Lee, 5★ Open Data, dereference URI (303, content negotiation) |

## 3. Hiểu dự án

Đọc `ARCHITECTURE.md`: §1 (4 tầng), §3.2 (cây lớp), §3.6 (đồ thị một thực thể), §5.2 (suy luận), §6.6 (KG-RAG),
§8 (quyết định thiết kế). Ontology: `ontology/220-athlete.ttl`, `ontology/100-core-classes.ttl`.

**Câu chuyện xuyên suốt:** Wikidata + viwiki → seeds/enrich → build RDF → validate → suy luận OWL 2 RL →
`asserted.nt` + `inferred.nt` → rdflib trong bộ nhớ → FastAPI `/sparql` + UI.

**Bốn cơ chế suy luận (ví dụ thật):**

| Trên UI thấy | Nhờ tiên đề | Số liệu |
|---|---|---|
| Cầu thủ có type `dbo:SoccerPlayer` | `vio:FootballPlayer ⊑ dbo:SoccerPlayer` | 0 → 611 |
| Nhãn "Cầu thủ đội tuyển" | `FootballPlayer ⊓ ∃careerStation.NationalTeamStation ⊑ NationalTeamPlayer` | 0 → 486 |
| Cạnh `playedFor` nối thẳng tới CLB | property chain `careerStation ∘ team` | 0 → 2.772 |
| CLB có `hasPlayer` | `owl:inverseOf playedFor` | 2.772 |

**Hai lần suy luận bắt được lỗi mô hình (§5.2):**
1. Đội tuyển bị suy ra là CLB → vi phạm disjointness → do domain của `ground` sai, đã đổi thành `vio:Organisation`.
2. Bỏ `tenant owl:inverseOf ground`: "từng thuê sân" khác "sân nhà" (gây kết quả sai cho "CLB nào sân nhà ở Hà Nội").

## 4. Câu hỏi dễ gặp theo từng màn

| Màn | Câu hỏi | Ý trả lời |
|---|---|---|
| Tổng quan | 131K triple, bao nhiêu là suy luận? | 89K khai báo + 42K suy luận + 549 ontology; tách file `data/parts/` |
| | Sao không dùng thẳng `dbo:`? | DBpedia thiếu CareerStation chi tiết, FormerProvince; `vio: ⊑ dbo:` nên sau suy luận vẫn truy vấn bằng `dbo:` |
| Thực thể (timeline) | Sao không nối thẳng cầu thủ → CLB? | Quan hệ n-ngôi / reification: có năm, số trận, bàn, cho mượn → cần nút `CareerStation`; cạnh thẳng `playedFor` được suy ra bằng property chain |
| Thực thể (LOD) | `owl:sameAs` lấy thế nào, có sai không? | Từ sitelink enwiki của chính item Wikidata, không đoán theo tên; `check_sameas` loại trang định hướng/danh sách; 777 → DBpedia, 990 → Wikidata, mô tả bằng VoID Linkset |
| | Sao reasoner bỏ `sameAs`? | OWL RL sinh `x sameAs x` cho mọi nút và có thể gộp nhầm thực thể |
| | 4★ hay 5★? | RDF là 4★; có link ra DBpedia/Wikidata thì đạt tiêu chí 5★ |
| Hỏi đáp | LLM có bịa không? | LLM chỉ sinh SPARQL; truy vấn chạy thật trên graph, trả lời dựa trên kết quả; lỗi/0 dòng thì cho LLM sửa (tối đa 2 lần) |
| | Không mạng / không LLM? | `demo_cache.json` cho 5 câu, SPARQL vẫn chạy thật (D5). **Nói trước, đừng để thầy tự phát hiện** |
| Bản đồ / sáp nhập | Còn bao nhiêu tỉnh? | 34, lọc `FILTER NOT EXISTS { ?p a vio:FormerProvince }`; `successor`/`predecessor` giữ lịch sử |
| SPARQL | Endpoint chuẩn chưa? | SPARQL 1.1 Protocol; chuẩn bị sẵn một lệnh curl để demo |

Phần crawl/infobox (§4) là của team: chỉ cần một câu — "chọn thực thể qua Wikidata, lấy infobox viwiki bằng
mwparserfromhell, có thứ tự ưu tiên Wikidata/infobox". Bị hỏi sâu thì chuyển cho bạn phụ trách.

## 5. Số liệu nên thuộc

18 lớp `vio:` · 54 thuộc tính (26 object + 28 datatype) · 990 thực thể seed · 8.624 tài nguyên · 131.233 triple ·
777 sameAs → DBpedia · 0 lỗi validation · reasoner ~100 giây.

## 6. Lộ trình

1. **Ngày 1:** kiến thức nền (§2); đọc hai file ontology ở §3.
2. **Ngày 2:** chạy `serve`, lấy Đặng Quang Huy, **tự viết SPARQL tái tạo mọi thứ UI hiện** (timeline, `playedFor`,
   sameAs, type suy luận). Làm được bước này là trả lời được hầu hết câu "từ đâu ra".
3. **Ngày 3:** tập kể chuyện demo theo bảng §4; nhờ một bạn đóng vai thầy hỏi vặn.
