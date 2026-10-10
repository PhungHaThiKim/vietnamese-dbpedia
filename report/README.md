# report/

Nguồn LaTeX của báo cáo môn Semantic Web, đề tài 2: *Build a DBpedia version for Vietnamese
language*. Viết bằng tiếng Anh, trình bày theo format NeurIPS 2024 (`neurips_2024.sty`): `main.tex`
chỉ chứa thứ tự `\input`, `preamble.tex` chứa package và khối tiêu đề, mỗi chương một file trong
`sections/`.

## Format NeurIPS

- `neurips_2024.sty` nạp với `[preprint,nonatbib]`. `preprint` in tên tác giả và bỏ số dòng (chế độ
  mặc định là bản nộp ẩn danh, có đánh số dòng); `nonatbib` giữ kiểu trích dẫn số của IEEEtran.
- Khổ US Letter, vùng chữ 5,5 × 9 inch, chữ 10pt, tiêu đề nằm giữa hai đường kẻ. File style lấy từ
  bản NeurIPS 2024 của bài mẫu, với ba chỗ sửa: khối tác giả của chế độ ẩn danh trả về nguyên bản
  (Anonymous Author(s)); `\@notice` được `\providecommand` trước khi định nghĩa lại, vì LaTeX từ 2025
  không còn sẵn lệnh này; và thân `\@notice` lấy lại bản chính thức (hộp nổi ở cuối trang 1).
- Tác giả khai báo bằng `\author{… \And …}` trong `preamble.tex`: dòng đầu in đậm là tên, dòng sau
  là mã số sinh viên. Thông tin môn học, nhóm, giảng viên và trường nằm ở dòng chú thích cuối trang 1,
  chỗ NeurIPS in tên hội nghị (`\@noticestring`).
- Font: NeurIPS dùng Times và Helvetica, hai font này không có glyph T5 cho tiếng Việt, nên preamble
  dùng TeX Gyre Termes và Heros (cùng thiết kế, có T5). Chữ mono (IRI, code) vẫn là Latin Modern.
- Vùng chữ hẹp hơn bản A4 cũ (13,97 cm so với 15 cm): Hình 1, Hình 3, Bảng 3 và Bảng 8 nằm trong
  `adjustbox{max width=\textwidth}`; Hình 4 chia theo tỉ lệ `\textwidth`; khối `Verbatim` dùng chữ
  8pt và `samepage`, dòng dài nhất khoảng 90 ký tự.

## Build

Cần MiKTeX hoặc TeX Live có `latexmk`:

```
make            # -> main.pdf
make watch      # build lại mỗi khi lưu
make clean      # xoá file phụ, giữ PDF
```

Hoặc chạy thẳng `latexmk -pdf main.tex`. Không có `make` thì chạy `latexmk -c` để dọn file phụ.

Tiếng Việt chạy được với pdflatex nhờ encoding T5 đặt làm mặc định trong `preamble.tex`. Khối mã dùng
`fancyvrb` (`Verbatim`), không dùng `listings`, vì `listings` không đọc được ký tự UTF-8 có dấu.

## Cấu trúc

```
main.tex            thứ tự \input
neurips_2024.sty    style NeurIPS 2024
preamble.tex        nạp style, package, macro \term{} \fillin{} \apx, màu, khối tiêu đề và tác giả
references.bib      tài liệu tham khảo (IEEEtran), mục nào cũng được trích
report_numbers.py   in mọi con số mà report trích, tính từ data/
sections/
  00-abstract.tex      tóm tắt và từ khoá
  01-introduction.tex  bối cảnh, phạm vi, đóng góp, bảng đối chiếu 5 yêu cầu của đề
  02-related-work.tex  DBpedia, Linked Data và 5 sao, Wikidata, OWL 2 RL, KG-QA
  03-method.tex        kiến trúc, ontology, thu thập, chuyển sang RDF, liên kết, kiểm tra và suy luận
  04-publishing.tex    máy chủ, URI dereference được, SPARQL endpoint /sparql và lệnh query, giao diện, hỏi đáp
  05-evaluation.tex    thống kê, độ phủ, tác động của suy luận, test, kiểm tra liên kết DBpedia, CQ, 5 sao
  06-discussion.tex    quyết định thiết kế và hạn chế
  07-conclusion.tex
figures/            ảnh chụp giao diện (ui_entity.png, ui_entity_graph.png, ui_ask.png), hình RDFS (rdfs_graph.tex)
                    và đồ thị RDF một thực thể (entity_graph.tex)
```

Ba hình sơ đồ vẽ bằng TikZ:
- kiến trúc: ngay trong `03-method.tex`;
- đồ thị RDF một thực thể (Hình 3): `figures/entity_graph.tex`, vẽ theo ký hiệu bài giảng (02_RDF tr.10–14,
  04_LOD tr.37): elip là tài nguyên, chữ nhật là literal, cạnh ghi qname. Slide 10 của bản editable dùng cùng
  nút, cạnh và toạ độ;
- đồ thị RDFS (Hình 2): `figures/rdfs_graph.tex`, vẽ theo kiểu bài giảng (hình elip, `rdfs:Class` và
  `rdf:Property` ở trên, đường kẻ ngang tách schema với dữ liệu) cho một phần ontology và ví dụ Công
  Phượng. Dùng chung với slide 6; màu đặt trong `preamble.tex` của từng thư mục, cỡ chữ trong hình
  là cỡ tuyệt đối nên hai nơi hiển thị giống nhau. Cây lớp đầy đủ kèm số thực thể nằm ở Bảng 3.

## Số liệu

Mọi con số trong report lấy từ dataset hiện tại. Sau khi chạy lại pipeline, chạy:

```
python report/report_numbers.py             # từ thư mục gốc của repo
python report/report_numbers.py --dbpedia   # thêm kiểm tra owl:sameAs trên dbpedia.org (cần mạng)
```

rồi so với các bảng trong `sections/`. Mỗi nhóm số trong output ghi nhãn bảng tương ứng
(`tab:dataset`, `tab:reasoning`, `tab:links`…). Phần kiểm tra liên kết in luôn danh sách 12 liên kết
trỏ tới trang đổi hướng và 32 liên kết chưa có trên DBpedia.

Số đo thời gian chỉ đúng với máy đã chạy: suy luận 35 s (lấy từ `vietnamese_dbpedia_stats.json`),
truy vấn tìm theo tên viết phẳng 10,7 s so với 0,27 s khi đặt trong subquery, và `pytest` 62 test
trong khoảng 25 s. Giao diện có thêm 90 test (`pytest ui/tests`, khoảng 30 s), nên tóm tắt ghi 152 test.

Listing 2 và 3 (mục 4.1, 4.2) chép từ máy chủ giao diện mới đang chạy (`python -m ui.api`, cổng 8000): `curl` gửi truy vấn tới `/sparql` (kết quả CSV) và
`python -m vidbpedia query` in bảng. Truy vấn đầu chỉ dùng từ vựng `dbo:`, nên mọi kết quả đều đến từ
triple suy luận (`asserted.nt` không có `dbo:Stadium` hay `dbo:seatingCapacity`). Truy vấn thứ hai cho
đúng đáp án của câu hỏi "tỉnh nào có nhiều cầu thủ nhất" ở Bảng 10.

## Ảnh chụp giao diện

Chụp bằng Chrome headless (DevTools Protocol) trên giao diện React của `python -m ui.api` (cổng 8000),
khung nhìn rộng 1200 px (trang thực thể hiện hai cột), độ phân giải 2x; mỗi ảnh rộng hết khổ chữ.
- `ui_entity.png` (Hình 4a): phần đầu trang Nguyễn Công Phượng, cây phân lớp và thẻ "Liên kết dữ liệu mở";
  ẩn phần tóm tắt cho gọn (chú thích hình đã ghi rõ).
- `ui_entity_graph.png` (Hình 4b): thông tin chính, sự nghiệp và đồ thị lân cận kéo thả.
- `ui_ask.png` (Hình 5): màn Hỏi đáp với câu "Cầu thủ nào từng chơi cho Than Quảng Ninh?", LLM là `gpt-4o`;
  câu trả lời, thanh sáu bước, bước 2 (SPARQL), thuật ngữ của bước 3 và ô so sánh của bước 4 (39 dòng có
  suy luận, 0 dòng chỉ khai báo); ẩn bước 1, danh sách kiểm tra của bước 3 và dòng "lấy lại kết quả trong
  phiên" (chú thích hình ghi rõ phần bị ẩn).

## Trạng thái

Build sạch với MiKTeX 25.12 (pdflatex, bibtex, pdflatex ×2): 15 trang, đúng bằng giới hạn của đề
(≤ 15), 0 lỗi LaTeX, 0 tham chiếu hay trích dẫn chưa giải, 0 cảnh báo font, 0 dòng tràn lề. Tài liệu
tham khảo theo sau mục Conclusion ở cỡ `\small`, như bài NeurIPS; trang 15 chỉ còn khoảng một dòng.
Thêm nội dung thì phải bớt chỗ khác để giữ 15 trang.
`latexmk` của MiKTeX cần Perl; máy không có Perl thì chạy tay:

```
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

## Trước khi nộp

- Khối tiêu đề đã đủ: 4 thành viên nhóm 23 (tên và mã số), giảng viên Dr. Do Ba Lam ở dòng chú
  thích trang 1 (`preamble.tex`). Macro `\fillin{}` vẫn còn trong preamble nếu cần chỗ trống chờ điền.
- Nếu đổi ngày nộp thì sửa tháng trong `\@noticestring` ở `preamble.tex` (NeurIPS không in `\date`).
