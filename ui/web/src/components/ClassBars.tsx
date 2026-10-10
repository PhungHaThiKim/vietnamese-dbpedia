import { Link } from "react-router-dom";
import type { ClassRow } from "../api/types";
import { formatNumber } from "../utils/format";

const MIN_BAR_PCT = 0.6; // lớp rất nhỏ (1 thực thể) vẫn nhìn thấy được

/** Cây lớp vio: dạng thanh ngang thụt lề; độ dài ∝ số thực thể, chia đoạn khai báo / suy luận. Lớp cha dbo: ghi bên dưới tên. */
export function ClassBars({ rows, showInferred }: { rows: ClassRow[]; showInferred: boolean }) {
  const depth = new Map<string, number>();
  for (const r of rows) depth.set(r.id, r.parent ? (depth.get(r.parent) ?? 0) + 1 : 0);
  const max = Math.max(...rows.map((r) => r.total), 1);
  const pct = (n: number) => (n === 0 ? 0 : Math.max((n / max) * 100, MIN_BAR_PCT));

  return (
    <ul className="classbars">
      {rows.map((r) => {
        const inferredOnly = r.asserted === 0;
        const faded = !showInferred && inferredOnly;
        // gốc ghi cả chuỗi lớp cha DBpedia: vio:Person ⊑ dbo:Person ⊑ dbo:Animal
        const chain = [r.dbo.join(", "), ...r.dboUp];
        return (
          <li key={r.id} className={faded ? "faded" : ""} style={{ paddingLeft: (depth.get(r.id) ?? 0) * 18 }}>
            <div className="cb-name">
              <Link className="cb-link" to={`/ontology#${r.id.replace(/^vio:/, "")}`} title="Xem định nghĩa lớp trong trang Ontology">
                <strong>{r.label.replace(/ \(.*\)$/, "")}</strong> <code>{r.id}</code>
              </Link>
              {r.dbo.length > 0 && (
                <span className="cb-sub" title={chain.map((d) => r.dboLabels[d] ?? d).join(" ⊑ ")}>
                  ⊑ {chain.join(" ⊑ ")} <span className="cb-ext">DBpedia</span>
                </span>
              )}
            </div>
            <div className="cb-track" title={`${formatNumber(r.asserted)} khai báo · ${formatNumber(r.total - r.asserted)} suy luận`}>
              <span className="cb-asserted" style={{ width: `${pct(r.asserted)}%` }} />
              {showInferred && r.total > r.asserted && (
                <span className="cb-inferred" style={{ width: `${pct(r.total) - pct(r.asserted)}%` }} />
              )}
            </div>
            <div className="cb-num">
              {formatNumber(showInferred ? r.total : r.asserted)}
              {faded && <span className="cb-hint">chỉ nhờ suy luận</span>}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
