# slides/

Bộ slide Beamer cho báo cáo môn Semantic Web, đề tài 2: *Build a DBpedia version for Vietnamese
language*. Cùng khuôn với slide luận văn (SSI-DDI): theme Madrid, bảng màu đỏ HUST, logo HUST ở góc
dưới trái và số trang ở góc dưới phải, tỉ lệ 4:3. Slide viết tiếng Anh, ghi chú thuyết trình viết
tiếng Việt. Có 20 slide.

## Build

```
latexmk -pdf main.tex     # -> main.pdf   (hoặc `make` nếu máy có make)
python make_pptx.py       # -> Vietnamese-DBpedia-slides.pptx, từ main.pdf + SPEAKER_NOTES.md
latexmk -c                # dọn file phụ, giữ PDF
```

`make_pptx.py` biến mỗi trang PDF thành một ảnh tràn khung (300 dpi, 4:3) và chép mục
`### Slide N` tương ứng của `SPEAKER_NOTES.md` vào phần ghi chú, để xem ở Presenter View. Cần
python-pptx và PyMuPDF (có sẵn ở python base của anaconda). Sửa PDF hay ghi chú thì chạy lại script,
và giữ số slide trong `SPEAKER_NOTES.md` khớp với bộ slide; script dừng nếu có ghi chú trỏ quá slide cuối.

Bản PPTX là ảnh, không sửa chữ trong PowerPoint được. Muốn sửa thì sửa LaTeX rồi build lại.

## Cấu trúc

```
main.tex                  thứ tự \input
preamble.tex              theme Madrid, màu HUST, chân trang, macro \term{} \hl{} \fillin{}
sections/                 4 phần nối tiếp, mỗi phần một người trình bày
  00-title.tex            (1)      Phần 1 · Trung: bìa HUST
  01-introduction.tex     (2–4)    Phần 1 · Trung: đề bài, miền dữ liệu, kiến trúc
  02-collection.tex       (5)      Phần 1 · Trung: thu thập từ Wikidata và MediaWiki API
  03-ontology.tex         (6–7)    Phần 2 · Phụng: đồ thị RDFS (schema + dữ liệu), tiên đề OWL
  04-extraction.tex       (8–9)    Phần 2 · Phụng: wikitext → RDF, chuyển sang 4 sao (trước/sau)
  05-reasoning.tex        (10–11)  Phần 2 · Phụng: một thực thể (10) · Phần 3 · Hoàng: kiểm tra, suy luận OWL 2 RL (11)
  06-linking.tex          (12–14)  Phần 3 · Hoàng: liên kết DBpedia, 303 + content negotiation, 5 sao
  07-interface.tex        (15–16)  Phần 3 · Hoàng: giao diện 4 tab, hỏi đáp bằng LLM
  08-evaluation.tex       (17–18)  Phần 4 · Dũng: demo web (trước slide 17), competency questions, hạn chế
  09-conclusion.tex       (19–20)  Phần 4 · Dũng: kết luận, cảm ơn
SPEAKER_NOTES.md          người trình bày, nói gì ở từng slide, kịch bản và thời lượng video 3–5 phút
make_pptx.py              bản PowerPoint có ghi chú thuyết trình
figures/                  hình HUST và ảnh chụp giao diện
```

## Số liệu

Mọi con số trong slide lấy từ report (`../report/`). Sau khi chạy lại pipeline, chạy
`python report/report_numbers.py` ở thư mục gốc của repo, rồi sửa cả report lẫn slide.

## Hình

- `hust_closing.png`, `hust_emblem.png`: chép nguyên từ slide luận văn.
- `hust_title.png`: bìa HUST của slide luận văn, đã xoá bốn dòng chữ (tên luận văn, đề tài, học viên,
  giáo viên hướng dẫn) bằng các khung trắng; logo, vòng chấm và dòng "ONE LOVE. ONE FUTURE." giữ
  nguyên. Chữ trên bìa mới đặt bằng TikZ trong `00-title.tex`.
- `ui_resource.png`, `ui_sparql.png`: ảnh giao diện Gradio cũ, chỉ bản LaTeX còn dùng. Bản editable dùng ảnh
  mới chụp trên giao diện React của `python -m ui.api` (trang Thực thể và trang SPARQL, khung 760 px, 2x).

Slide 3 và slide 10 của bản editable vẽ theo ký hiệu bài giảng: lớp và tài nguyên là elip, literal là chữ nhật,
cạnh ghi qname (02_RDF tr.10–14, 03_RDFS tr.22). Slide 10 dùng cùng nút, cạnh và toạ độ với Hình 3 của report
(`../report/figures/entity_graph.tex`).

Slide 6 dùng chung hình đồ thị RDFS (kiểu bài giảng) với report: `../report/figures/rdfs_graph.tex`,
màu HUST đặt trong `preamble.tex`. Vì vậy build slide cần có thư mục `report/` bên cạnh.

Các sơ đồ còn lại (kiến trúc, chuỗi quan hệ, một thực thể, luồng hỏi đáp) vẽ bằng TikZ ngay trong `sections/`:
khối nền hồng viền đỏ là các bước của hệ thống, khối xám là dữ liệu, khối viền đứt là hệ thống ngoài;
nét đỏ đứt là triple suy luận, nét xanh là liên kết sang dataset khác.

## Trước khi trình bày

- Bìa đã đủ: 4 thành viên nhóm 23 và giảng viên Dr. Do Ba Lam (`sections/00-title.tex`). Sửa bìa
  thì build lại PDF rồi chạy `make_pptx.py`.
- Đọc phần "Kịch bản video" trong `SPEAKER_NOTES.md`: nói đủ mọi slide cộng demo web của Dũng mất khoảng
  5 phút 20 giây; cách rút về khoảng 4 phút 55 giây ghi ở đó.
- `Vietnamese-DBpedia-slides-editable.pptx` là bản chính và đã khớp với `main` (giao diện React ở cổng
  8000): slide 2, 4, 7, 11, 13, 14, 15, 16, 17, 18, 19 đã sửa, ghi chú thuyết trình của từng slide chép từ
  `SPEAKER_NOTES.md` (cũng đã cập nhật, kể cả kịch bản demo). Lần sửa ngày 10/10/2026 theo ontology mới:
  859 triple ontology, tổng 131.543 triple, 152 test, suy luận 35 s; slide 7 có tiên đề dạng giao
  `FootballPlayer ⊓ ∃careerStation.NationalTeamStation` và quy tắc hai tầng theo bài giảng (dùng lại `dbo:`,
  không có `vio:Animal`); slide 15 ghi cây lớp kèm lớp cha DBpedia. Bản LaTeX và bản PPTX dạng ảnh vẫn mô tả
  giao diện Gradio cũ và số liệu cũ; muốn dùng thì phải sửa các slide trên cho khớp.
