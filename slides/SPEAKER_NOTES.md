# Chú thích thuyết trình — Vietnamese DBpedia (20 slide)

Mỗi slide gồm: **Nói** (mạch nói), **Số phải trúng** (con số cần đọc chính xác), và **Nếu bị hỏi**
ở các slide then chốt. Số slide khớp với số ở góc dưới phải. Mọi con số lấy từ report (`report/`),
tính lại được bằng `python report/report_numbers.py`.

## Bốn phần, bốn người

Bộ slide chia thành bốn phần nối tiếp theo mạch của pipeline. Mỗi người trình bày một đoạn liền mạch
và trả lời câu hỏi về phần của mình. Phần cuối mở đầu bằng demo web trực tiếp.

| Phần | Người trình bày | Slide | Nội dung | Thời lượng |
|---|---|---|---|---|
| 1. Đề tài, kiến trúc và thu thập dữ liệu | Do Ngoc Trung | 1–5 | đề bài, miền dữ liệu, kiến trúc, thu thập | 1:05 |
| 2. Ontology, RDF 4 sao và một thực thể | Ha Thi Kim Phung | 6–10 | đồ thị RDFS, tiên đề OWL, trích infobox, 4 sao, một thực thể | 1:35 |
| 3. Kiểm tra, suy luận, Linked Data và giao diện | Bui Duc Phan Hoang | 11–16 | kiểm tra, suy luận, liên kết DBpedia, URI, 5 sao, giao diện, hỏi đáp | 1:35 |
| 4. Demo web, đánh giá, hạn chế và kết luận | Do Hoang Dung | demo, 17–20 | demo trực tiếp, câu hỏi năng lực, hạn chế, hướng phát triển, kết luận | 1:05 |
| | | | **Tổng** | **≈ 5:20** |

Mạch tổng: đề bài → miền dữ liệu → kiến trúc → thu thập → đồ thị RDFS và tiên đề → trích infobox →
chuyển sang 4 sao → một thực thể → kiểm tra, suy luận → liên kết DBpedia, URI, 5 sao → giao diện, hỏi
đáp → demo web → đánh giá, hạn chế → kết luận. Bốn chỗ dừng lâu: **slide 7** (tiên đề OWL), **slide 9**
(4 sao), **slide 10** (một thực thể), **slide 12** (liên kết DBpedia).

## Kịch bản video 3–5 phút

Nói đủ mọi slide cộng 30 giây demo thì mất khoảng 5 phút 20 giây, quá giới hạn 5 phút. Để còn khoảng
4 phút 55 giây: giữ demo trong 25 giây, và chỉ chiếu slide 5 (Trung) và slide 13 (Hoàng) mà không nói
(bớt khoảng 20 giây). Mỗi người có thể ghi âm phần mình riêng rồi ghép.

| Slide | Người | Thời lượng | Slide | Người | Thời lượng |
|---|---|---|---|---|---|
| 1 Title | Trung | 0:10 | 11 Validation, reasoning | Hoàng | 0:20 |
| 2 Assignment | Trung | 0:20 | 12 Linking | Hoàng | 0:20 |
| 3 Why this domain | Trung | 0:10 | 13 Dereferenceable IRIs | Hoàng | 0:10 |
| 4 Architecture | Trung | 0:15 | 14 Five stars | Hoàng | 0:10 |
| 5 Collection | Trung | 0:10 | 15 Web interface | Hoàng | 0:15 |
| 6 RDFS graph | Phụng | 0:20 | 16 Question answering | Hoàng | 0:20 |
| 7 OWL axioms | Phụng | 0:20 | Demo web (quay màn hình) | Dũng | 0:30 |
| 8 Wikitext to RDF | Phụng | 0:15 | 17 Evaluation | Dũng | 0:10 |
| 9 Transform to 4★ | Phụng | 0:20 | 18 Limitations | Dũng | 0:10 |
| 10 One entity | Phụng | 0:20 | 19 Conclusion | Dũng | 0:10 |
| | | | 20 Thank you | Dũng | 0:05 |

**Demo web (phần của Dũng, ngay sau slide 16, quay màn hình 25–30 giây):** chạy sẵn
`python -m ui.api` (cổng 8000) trước khi quay, và bấm câu mẫu Than Quảng Ninh một lần để server nhớ kết
quả. Mở `http://127.0.0.1:8000/entity/Nguyễn_Công_Phượng`: lớp khai báo, lớp suy luận, thẻ Liên kết dữ
liệu mở; kéo một nút trong đồ thị lân cận, rồi tắt công tắc "Hiện suy luận" để các cạnh `playedFor` nét
đứt biến mất. Sang Hỏi đáp, bấm câu mẫu "Cầu thủ nào từng chơi cho Than Quảng Ninh?": câu trả lời hiện
ngay dưới ô hỏi, bước 4 cho thấy 39 dòng có suy luận và 0 dòng chỉ khai báo. Hỏi đáp dùng key LLM trong
`.env` (đang là gpt-4o); LLM lỗi thì câu mẫu vẫn chạy bằng SPARQL viết sẵn.

---

## Phần 1 — Do Ngoc Trung: đề tài, kiến trúc và thu thập dữ liệu

### Slide 1 — Title
**Nói:** Chào thầy và các bạn. Nhóm 23 trình bày đề tài 2 của môn Semantic Web: xây dựng một phiên bản
DBpedia cho tiếng Việt. Mình là Trung, mở đầu bằng đề bài, kiến trúc và cách nhóm thu thập dữ liệu.

### Slide 2 — The Assignment and What We Built
**Nói:** Đề bài có năm yêu cầu, và bảng này cho thấy nhóm đáp ứng từng yêu cầu ra sao: ontology
`vio:` 18 lớp, 990 bài viết tiếng Việt, 131 nghìn triple RDF, 777 liên kết sang DBpedia tiếng Anh,
và giao diện truy vấn. Nhóm không trích toàn bộ Wikipedia tiếng Việt mà chọn một miền và làm sâu.
**Số phải trúng:** 18 lớp, 54 thuộc tính; 990 bài; 131.543 triple; 777 liên kết.

### Slide 3 — Why This Domain?
**Nói:** Miền được chọn là bóng đá Việt Nam, tỉnh thành và đại học, vì các thực thể trỏ lẫn nhau:
cầu thủ, câu lạc bộ, sân nhà, tỉnh. 97% bài có infobox, 78% có bài tiếng Anh để liên kết.
**Số phải trúng:** 611 cầu thủ, 110 tỉnh (34 hiện hành); 97%, 78%.
**Nếu bị hỏi** "sao không chọn thực thể theo thể loại Wikipedia?": thể loại do người viết gán, không
nhất quán; Wikidata cho lớp (`P31`) và quốc gia (`Q881`) chính xác hơn.

### Slide 4 — Architecture
**Nói:** Hệ thống có bốn tầng, mỗi bước là một lệnh. Chỉ tầng thu thập gọi mạng; mọi thứ được cache
nên dựng lại được mà không cần Internet.
**Số phải trúng:** 6 lệnh: seeds, enrich, ontology, build, postprocess, serve.

### Slide 5 — Collecting Entities and Articles
**Nói:** Mỗi lớp là một truy vấn Wikidata; đây là truy vấn cho cầu thủ. Sau đó lấy bài viết qua
MediaWiki API: abstract, thể loại, redirect và tham số infobox. Request được giãn cách và cache lại.
Tiếp theo, Phụng trình bày ontology và cách chuyển dữ liệu sang RDF.
**Số phải trúng:** 2.588 đích liên kết trong infobox, 71 trang định hướng.
**Nếu bị hỏi** "sao không dùng bản dump của Wikipedia?": với 990 bài, API nhanh hơn và chỉ lấy đúng
phần cần; cache SQLite và cờ `--offline` cho kết quả lặp lại được như dùng dump.

## Phần 2 — Ha Thi Kim Phung: ontology, RDF 4 sao và một thực thể

### Slide 6 — Ontology vio: as an RDFS Graph
**Nói:** Mình là Phụng, phụ trách ontology và cách chuyển dữ liệu sang RDF. Đây là một phần ontology
vẽ dạng đồ thị RDFS. Phía trên đường kẻ là schema: lớp là `rdfs:Class`, thuộc tính là `rdf:Property`,
nối bằng `subClassOf` và `subPropertyOf`; `careerStation` có domain là cầu thủ, range là chặng thi
đấu. Phía dưới là dữ liệu: Công Phượng có chặng thi đấu ở Hoàng Anh Gia Lai, quê Nghệ An. Nét đứt là
triple RDFS suy ra: Công Phượng cũng là `dbo:Person`. Trên cùng là `dbo:Animal`: DBpedia tự đặt
`dbo:Person` dưới `dbo:Animal`, nhóm giữ nguyên chuỗi lớp đó.
**Số phải trúng:** toàn bộ ontology có 18 lớp, 54 thuộc tính; lớp nào cũng là lớp con của một lớp DBpedia.
**Nếu bị hỏi** "vì sao Công Phượng là `dbo:Person`?": luật rdfs9, kiểu được truyền lên theo
`subClassOf`: FootballPlayer ⊑ Athlete ⊑ Person ⊑ dbo:Person, và tiếp lên `dbo:Animal` (luật rdfs11).

### Slide 7 — OWL Axioms Do the Work ← DỪNG
**Nói:** Các tiên đề OWL làm phần lớn công việc. Chuỗi thuộc tính `careerStation` rồi `team` cho
2.772 cạnh "từng thi đấu cho". Ràng buộc tồn tại xếp 486 cầu thủ vào lớp tuyển thủ quốc gia. Ràng
buộc "với mọi" gán lớp CLB cho 154 đội không phải seed. Tiên đề tách lớp còn giúp phát hiện hai lỗi
mô hình hoá.
**Số phải trúng:** 2.772; 486; 154; 2 lỗi.
**Nếu bị hỏi** "vì sao không đặt domain cho `latitude` hay `province`?": CLB và trường đại học cũng có
toạ độ và tỉnh; nếu domain là `Location` thì reasoner sẽ suy ra CLB là địa điểm, trái với tiên đề
tách lớp.
**Nếu bị hỏi** "vì sao có nhãn Động vật mà không có `vio:Animal`?": ontology hai tầng theo bài giảng. Tầng
trên dùng lại lớp `dbo:` (thêm nhãn tiếng Việt, `rdfs:isDefinedBy dbo:`); chỉ tạo lớp `vio:` khi cần tiên
đề như domain hay tách lớp. `vio:` nối lên `dbo:` bằng `subClassOf` chứ không `equivalentClass`, để tiên đề
của nhóm chỉ ràng buộc dữ liệu của nhóm (anti-pattern Exclusivity). Tiên đề tuyển thủ quốc gia viết dạng
giao `FootballPlayer ⊓ ∃careerStation.NationalTeamStation` cũng theo lời giải của anti-pattern này.

### Slide 8 — From Wikitext to RDF
**Nói:** Infobox đi qua bốn bước: diễn giải template, đọc giá trị kiểu Việt như "16.361,2" hay dấu
cho mượn, ánh xạ khoá sang `vio:`, rồi chọn Wikidata hay infobox cho từng thuộc tính. Các hàng năm,
CLB, số trận, bàn thắng thành 3.382 chặng thi đấu.
**Số phải trúng:** 3.382 chặng của 601 cầu thủ; 24.605 triple infobox thô.
**Nếu bị hỏi** "khi Wikidata và infobox khác nhau thì lấy bên nào?": bảng `PRECEDENCE` quyết định;
Wikidata cho ngày, chiều cao, dân số, sức chứa; infobox cho số áo, số sinh viên, khẩu hiệu.

### Slide 9 — Transform to 4★: One Infobox, Before and After ← DỪNG
**Nói:** Đây là bước chuyển sang 4 sao trên một infobox thật. Phía trên là wikitext: máy đọc được
nhưng chỉ là chữ, không có URI. Phía dưới là RDF: mỗi thứ có một IRI, kể cả chặng cho mượn ở Mito;
giá trị có kiểu, như ngày sinh là `xsd:date`; dấu "mượn" thành `onLoan true`; còn chiều cao lấy theo
Wikidata là 1,68 thay vì 1,69 của infobox.
**Số phải trúng:** 21/01/1995; Mito HollyHock 2016, 5 trận, 0 bàn, cho mượn.
**Nếu bị hỏi** "3 sao khác 4 sao ở đâu?": 3 sao là định dạng mở như CSV hay JSON; 4 sao là dùng URI
để định danh từng thứ, để người khác trỏ tới và tra được (303 ở slide 13).

### Slide 10 — One Entity, End to End ← DỪNG
**Nói:** Ghép lại, đây là Nguyễn Công Phượng dưới dạng đồ thị RDF, vẽ đúng ký hiệu bài giảng: elip là
tài nguyên, chữ nhật là literal, mỗi mũi tên là một triple ghi tên thuộc tính. Nét xám là dữ liệu khai báo:
nhãn, ngày sinh, tỉnh Nghệ An và chặng cho mượn năm 2016 sang Mito HollyHock. Nét đỏ đứt là phần suy luận:
kiểu `dbo:SoccerPlayer`, cạnh `playedFor` từ chuỗi thuộc tính, và Mito được xếp vào lớp CLB nhờ ràng buộc
∀ của `ClubStation`. Nét xanh là liên kết `owl:sameAs` sang DBpedia và Wikidata. Tiếp theo, Hoàng trình
bày phần kiểm tra, suy luận và Linked Data.
**Số phải trúng:** 11 chặng thi đấu; chặng mượn 2016: 5 trận, 0 bàn.
**Nếu bị hỏi** "chặng thi đấu là gì trong RDF?": một tài nguyên trung gian cho quan hệ nhiều ngôi (cầu thủ,
đội, năm, số trận), như nút trung gian ở slide 02_RDF và mẫu "Roles taken at a time" ở slide 07; nhóm đặt
IRI cho nó thay vì nút rỗng để nó cũng tra được.

## Phần 3 — Bui Duc Phan Hoang: kiểm tra, suy luận, Linked Data và giao diện

### Slide 11 — Validation and OWL 2 RL Reasoning
**Nói:** Mình là Hoàng, phụ trách kiểm tra chất lượng, suy luận, Linked Data và giao diện. Trước khi
xuất, tám hàm kiểm tra chạy trên dữ liệu: lần dựng cuối không có lỗi nào. Suy luận thêm 41.730 triple
trong 35 giây, nhờ đó truy vấn bằng từ vựng DBpedia mới có kết quả. Suy luận còn bắt được hai lỗi mô
hình hoá mà nhóm đã sửa.
**Số phải trúng:** 0 lỗi, 0 cảnh báo; 152 test (62 của pipeline, 90 của giao diện); +41.730 triple.
**Nếu bị hỏi** về hai lỗi: (1) đội tuyển bị suy ra là CLB vì domain của `ground` đặt sai; (2) khai báo
`tenant` là nghịch đảo của `ground` làm sai sân nhà, vì ô "bên thuê" liệt kê mọi đội từng dùng sân.
**Nếu bị hỏi** "sao bỏ `owl:sameAs` và functional khỏi reasoner?": OWL 2 RL sinh `x sameAs x` cho mọi
nút và gộp các thực thể có cùng giá trị functional; functional được kiểm tra riêng ở bước validation.

### Slide 12 — Linking to English DBpedia ← DỪNG
**Nói:** Liên kết lấy từ sitelink tiếng Anh của chính item Wikidata, không ghép theo tên vì tên Việt
trùng nhiều. Có 777 liên kết sang DBpedia và 990 sang Wikidata. Nhóm kiểm tra cả 777 trên DBpedia
thật: 733 trỏ đúng bài viết, 44 còn lại lệch vì DBpedia lấy dữ liệu từ bản Wikipedia cũ hơn.
**Số phải trúng:** 777 / 990; 733 (94,3%); 12 đổi hướng, 32 chưa có.
**Nếu bị hỏi** "sửa 44 liên kết thế nào?": 12 cái đi theo `dbo:wikiPageRedirects` là sửa được; 32 cái
phải chờ bản DBpedia mới hoặc kiểm lại sau mỗi lần phát hành.

### Slide 13 — Dereferenceable IRIs
**Nói:** Mỗi IRI tra được như DBpedia: máy chủ trả 303, chuyển trình duyệt tới trang thực thể và chuyển
client RDF tới Turtle, N-Triples, JSON-LD hoặc RDF/XML theo header `Accept`. Endpoint `/sparql` theo
chuẩn SPARQL 1.1 Protocol, chạy cùng máy chủ ở cổng 8000.

### Slide 14 — Five Stars, Checked
**Nói:** Vậy dataset đạt đủ năm sao: giấy phép mở, máy đọc được, định dạng mở, URI cho mọi thứ, và
liên kết sang DBpedia, Wikidata. Lưu ý duy nhất: nhóm không sở hữu tên miền vi.dbpedia.org, nên IRI
chỉ mở được qua máy chủ của dự án.
**Nếu bị hỏi** "vậy sao đã đủ 4 sao?": 4 sao đòi hỏi định danh bằng URI và tra được; IRI của nhóm
dereference đúng chuẩn (303, content negotiation) trên máy chủ dự án; đưa lên Internet thật thì cần
một tên miền của nhóm hoặc dịch vụ như w3id.org.

### Slide 15 — Web Interface
**Nói:** Giao diện có năm trang: Tổng quan, Ontology, Thực thể, Hỏi đáp và SPARQL. Bên trái là trang
thực thể giống dbpedia.org/page: lớp khai báo và lớp suy luận, thẻ Liên kết dữ liệu mở, đồ thị lân cận
kéo thả được. Bên phải là trang SPARQL đang đếm thực thể theo lớp DBpedia, toàn bộ có nhờ suy luận: tắt
công tắc suy luận thì số `dbo:Person` từ 659 về 0.
*(Không demo ở đây: Dũng demo trực tiếp ngay sau slide 16.)*

### Slide 16 — Question Answering
**Nói:** Trang Hỏi đáp nhận câu hỏi tiếng Việt hoặc tiếng Anh và hiện câu trả lời ngay dưới ô hỏi, bên
dưới là sáu bước: nhận diện thực thể bằng chỉ mục tên, mô hình viết SPARQL với IRI đã nhận diện, kiểm
tra truy vấn, chạy có và không có suy luận, mô hình trả lời từ tối đa 30 dòng, và đồ thị bằng chứng.
Ví dụ hỏi ai từng chơi cho Than Quảng Ninh: 39 cầu thủ khi có suy luận, 0 khi chỉ dùng dữ liệu khai báo.
Sau đây, Dũng demo trực tiếp trên web.
**Số phải trúng:** 39 và 0; 10,7 giây xuống 0,27 giây nhờ subquery.
**Nếu bị hỏi** "LLM viết sai truy vấn thì sao?": truy vấn được parse trước khi chạy, chỉ SELECT/ASK, không
FROM/SERVICE; bước kiểm tra nêu tên IRI không có trong graph hoặc sai lớp và gửi lại cho mô hình sửa;
mọi lần thử đều hiện ra trên trang.

## Phần 4 — Do Hoang Dung: demo web, đánh giá, hạn chế và kết luận

### Slide 17 — Evaluation
**Nói (trước demo):** Mình là Dũng. Mình demo nhanh hệ thống đang chạy, rồi tổng kết đánh giá, hạn chế
và hướng phát triển.
**Demo (25–30 giây, quay màn hình):** chạy sẵn
`python -m ui.api` (cổng 8000) trước khi quay, và bấm câu mẫu Than Quảng Ninh một lần để server nhớ kết
quả. Mở `http://127.0.0.1:8000/entity/Nguyễn_Công_Phượng`: lớp khai báo, lớp suy luận, thẻ Liên kết dữ
liệu mở; kéo một nút trong đồ thị lân cận, rồi tắt công tắc "Hiện suy luận" để các cạnh `playedFor` nét
đứt biến mất. Sang Hỏi đáp, bấm câu mẫu "Cầu thủ nào từng chơi cho Than Quảng Ninh?": câu trả lời hiện
ngay dưới ô hỏi, bước 4 cho thấy 39 dòng có suy luận và 0 dòng chỉ khai báo. Hỏi đáp dùng key LLM trong
`.env` (đang là gpt-4o); LLM lỗi thì câu mẫu vẫn chạy bằng SPARQL viết sẵn.
**Nói (sau demo):** Graph trả lời đúng các câu hỏi năng lực, ví dụ còn 34 tỉnh thành, Nghệ An nhiều
cầu thủ nhất với 58 người. Mỗi câu là một test tự động.
**Số phải trúng:** 34; Nghệ An 58; 11 đội của Công Phượng.

### Slide 18 — Limitations and Future Work
**Nói:** Hạn chế chính: mới một miền 990 thực thể, 44 liên kết DBpedia cần sửa, endpoint `/sparql` chưa
giới hạn thời gian truy vấn, và chưa đo độ chính xác của hỏi đáp trên một bộ câu hỏi. Hướng tiếp theo:
giới hạn thời gian hoặc dùng triple store khi dữ liệu lớn, thêm lớp mới, và bộ câu hỏi tiếng Việt để đo
hỏi đáp.
**Nếu bị hỏi** "SPARQL endpoint ở đâu?": `http://127.0.0.1:8000/sparql`, đúng SPARQL 1.1 Protocol, gọi
bằng curl hay SPARQLWrapper; trong terminal thì dùng `python -m vidbpedia query`.

### Slide 19 — Conclusion
**Nói:** Tóm lại, nhóm đã xây dựng một DBpedia tiếng Việt năm sao cho ba miền dữ liệu. Suy luận OWL là
thứ giúp dữ liệu dùng chung được với DBpedia. Mã nguồn và dữ liệu có trên GitHub.

### Slide 20 — Thank you
**Nói:** Cảm ơn thầy và các bạn đã lắng nghe.
