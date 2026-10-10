import { useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useApi } from "../api/useApi";
import type { Overview } from "../api/types";
import { ClassBars } from "../components/ClassBars";
import { EntityLink } from "../components/EntityLink";
import { ErrorState, Loading } from "../components/States";
import { StatTile } from "../components/StatTile";
import { useInference } from "../context/InferenceContext";
import { formatNumber } from "../utils/format";

const PIPELINE = [
  "Wikipedia tiếng Việt + Wikidata",
  "Ánh xạ infobox",
  "RDF (ontology vio:)",
  "Suy luận OWL 2 RL",
  "owl:sameAs → DBpedia EN",
  "SPARQL / Linked Data",
];

// thuộc tính suy luận có chú thích riêng (cách suy luận ra chúng)
const PROP_NOTES: Record<string, string> = {
  "vio:playedFor": "property chain: careerStation ∘ team",
  "vio:hasPlayer": "owl:inverseOf vio:playedFor",
  "rdf:type": "lớp cha theo rdfs:subClassOf",
};

/** Tỷ lệ phần trăm; số liệu thiếu thì "—", mẫu số 0/null thì 0%. */
function percent(part: number | null, whole: number | null): string {
  if (part == null) return "—";
  if (!whole) return "0%";
  return `${Math.round((part / whole) * 100)}%`;
}

export function OverviewPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const resource = params.get("resource");
  const { showInferred } = useInference();
  const { data, error, loading } = useApi<Overview>(resource ? null : "/api/overview");

  // /resource/X (Linked Data) chuyển trình duyệt về /?resource=X; ở đây đổi thành trang thực thể
  useEffect(() => {
    if (resource) navigate(`/entity/${encodeURIComponent(resource)}`, { replace: true });
  }, [resource, navigate]);

  if (resource) return <Loading />;
  if (loading) return <Loading text="Đang tải số liệu dataset…" />;
  if (error || !data) return <ErrorState message={error ?? "Không có dữ liệu."} />;

  const { stats, byClass, inferredByPredicate, featured, questions } = data;
  const maxInferred = Math.max(...inferredByPredicate.map((p) => p.count), 1);
  const seg = (n: number | null) => `${n && stats.total ? (n / stats.total) * 100 : 0}%`;

  return (
    <div className="overview">
      {/* cùng phần đầu trang với giao diện Gradio */}
      <header className="ov-head">
        <h1 className="ov-title">Vietnamese DBpedia</h1>
        <p className="ov-lede">
          Dữ liệu có cấu trúc trích từ Wikipedia tiếng Việt và Wikidata, mô tả bằng ontology <code>vio:</code> căn theo
          DBpedia và liên kết <code>owl:sameAs</code> sang DBpedia tiếng Anh.
        </p>
      </header>

      <section className="tiles">
        <StatTile value={formatNumber(stats.total)} label="triple" />
        <StatTile value={formatNumber(stats.asserted)} label="khai báo" note="trích từ Wikipedia / Wikidata" />
        {showInferred && (
          <StatTile
            tone="inferred"
            value={formatNumber(stats.inferred)}
            label="suy luận"
            note={`+${percent(stats.inferred, stats.asserted)} so với khai báo${stats.reasoner ? ` · ${stats.reasoner}` : ""}`}
            onClick={() => document.getElementById("inference")?.scrollIntoView({ behavior: "smooth" })}
          />
        )}
        <StatTile value={formatNumber(stats.entities)} label="thực thể" note={`${formatNumber(stats.careerStations)} chặng sự nghiệp`} />
        <StatTile value={formatNumber(stats.sameAsDbpedia)} label="owl:sameAs → DBpedia EN" />
        <StatTile value={formatNumber(stats.sameAsWikidata)} label="owl:sameAs → Wikidata" />
        <StatTile
          tone="ok"
          value={formatNumber(stats.validationErrors)}
          label="lỗi kiểm tra"
          note={`${formatNumber(stats.validationWarnings)} cảnh báo`}
        />
      </section>

      <div className="split" aria-label="Cơ cấu triple">
        <span className="split-asserted" style={{ width: seg(stats.asserted) }} title="khai báo" />
        {showInferred && <span className="split-inferred" style={{ width: seg(stats.inferred) }} title="suy luận" />}
        <span className="split-ontology" style={{ width: seg(stats.ontology) }} title="ontology" />
      </div>
      <p className="split-legend">
        <span><i className="sw sw-asserted" />khai báo {formatNumber(stats.asserted)} ({percent(stats.asserted, stats.total)})</span>
        {showInferred && (
          <span><i className="sw sw-inferred" />suy luận {formatNumber(stats.inferred)} ({percent(stats.inferred, stats.total)})</span>
        )}
        <span><i className="sw sw-ontology" />ontology {formatNumber(stats.ontology)}</span>
      </p>

      <div className="cols">
        <section className="card">
          <h2>Cây lớp <code>vio:</code> ({byClass.length} lớp)</h2>
          <p className="muted small">
            Độ dài ∝ số thực thể (gồm cả lớp con). Đoạn đứt tím là phần chỉ có nhờ suy luận. Dòng “⊑” dưới tên là lớp cha DBpedia; gốc ghi
            cả chuỗi, ví dụ <code>dbo:Person ⊑ dbo:Animal</code>. Bấm tên lớp để xem định nghĩa ở trang <Link to="/ontology">Ontology</Link>.
          </p>
          <ClassBars rows={byClass} showInferred={showInferred} />
        </section>

        <section className="card" id="inference">
          <h2>Suy luận thêm được gì</h2>
          {showInferred ? (
            <>
              <p className="muted small">Số triple suy luận theo thuộc tính (top {inferredByPredicate.length}).</p>
              <ul className="hbars">
                {inferredByPredicate.map((p) => (
                  <li key={p.prop}>
                    <div className="hb-name">
                      <code>{p.prop}</code>
                      {p.label !== p.prop && <span className="hb-label">{p.label}</span>}
                      {PROP_NOTES[p.prop] && <span className="hb-note">{PROP_NOTES[p.prop]}</span>}
                    </div>
                    <div className="hb-track">
                      <span className="hb-bar" style={{ width: `${(p.count / maxInferred) * 100}%` }} />
                    </div>
                    <div className="hb-num">{formatNumber(p.count)}</div>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="muted">Đang ẩn suy luận. Bật “Hiện suy luận” ở thanh trên để xem bộ suy luận thêm được gì.</p>
          )}
        </section>
      </div>

      <ol className="pipeline" aria-label="Quy trình xây dựng">
        {PIPELINE.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>

      <section className="cols explore">
        <div className="card">
          <h2>Bắt đầu khám phá</h2>
          <ul className="plain">
            {featured.map((n) => (
              <li key={n.id}>
                <EntityLink node={n} /> <span className="muted small">{n.cls}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h2>Hỏi bằng tiếng Việt</h2>
          <ul className="plain">
            {questions.map((q) => (
              <li key={q}>
                <Link to={`/ask?q=${encodeURIComponent(q)}`}>{q}</Link>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
