import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import type {
  DboParents,
  Ontology,
  OntologyClass,
  OntologyProperty,
  ResourceTree,
  TreeClass,
  TreeGroup,
  TreeItem,
} from "../api/types";
import { useApi, type ApiState } from "../api/useApi";
import { IriTip } from "../components/IriTip";
import { ErrorState, Loading } from "../components/States";
import { Chevron, LeafMark, rowToggle } from "../components/TreeChevron";
import { formatNumber } from "../utils/format";

const FILTER_DEBOUNCE_MS = 250;
const DBO_NS = "http://dbpedia.org/ontology/";
const VIO_NS = "http://vi.dbpedia.org/ontology/";
const VRES_NS = "http://vi.dbpedia.org/resource/";
const INST_COLLAPSE_MIN = 30; // danh sách thực thể dài hơn thế này mới có mũi tên thu/mở riêng

/** "vio:playedFor" → "playedFor" (dùng trong công thức tiên đề cho gọn). */
const local = (id: string) => id.replace(/^vio:/, "");

// ============================================================================
// Cây tài nguyên (nội dung giống tab "Cây tài nguyên" của Gradio: vidbpedia/web/resource_tree.py;
// trạng thái mở/thu giữ trong React để có "Mở tất cả" / "Thu tất cả" và deep link #Term)
// ============================================================================

/** Trạng thái mở/thu của từng nút: `isOpen(key, mặc định)`; chưa bấm thì dùng mặc định. */
interface TreeCtl {
  isOpen: (key: string, def: boolean) => boolean;
  toggle: (key: string, def: boolean) => void;
}

function TermLink({ id, term }: { id: string; term: string }) {
  // mở định nghĩa Linked Data của team (/ontology/{term}) trong tab mới; rê chuột thấy IRI đầy đủ
  const iri = `${VIO_NS}${term}`;
  return (
    <IriTip iri={iri}>
      <a href={`/ontology/${encodeURIComponent(term)}`} target="_blank" rel="noopener noreferrer" title={iri}>
        <code>{id}</code>
      </a>
    </IriTip>
  );
}

/** Lớp DBpedia (dbo:Animal…): mở trang lớp trên dbpedia.org trong tab mới; rê chuột thấy nhãn @vi ("Động vật") và IRI. */
function DboLink({ id, label }: { id: string; label?: string }) {
  const iri = `${DBO_NS}${id.replace(/^dbo:/, "")}`;
  const tip = label ? `${label} · ${iri}` : iri;
  return (
    <IriTip iri={tip}>
      <a href={iri} target="_blank" rel="noopener noreferrer" title={tip}>
        <code>{id}</code> ↗
      </a>
    </IriTip>
  );
}

/**
 * Lớp cha DBpedia ghi sau dấu ⊑, không thành nút: cây chỉ vẽ được một cha (slide 03, đa kế thừa) nên cạnh của cây
 * chỉ nối lớp vio:. Gốc ghi cả chuỗi (vio:Person ⊑ dbo:Person ⊑ dbo:Animal); cuối có một nhãn DBpedia cho cả nhóm.
 */
function DboChain({ c }: { c: DboParents }) {
  if (c.dbo.length === 0) return null;
  return (
    <span className="ct-muted">
      {" "}
      ⊑{" "}
      {c.dbo.map((d, i) => (
        <span key={d}>
          {i > 0 && ", "}
          <DboLink id={d} label={c.dboLabels[d]} />
        </span>
      ))}
      {c.dboUp.map((d) => (
        <span key={d}>
          {" "}
          ⊑ <DboLink id={d} label={c.dboLabels[d]} />
        </span>
      ))}{" "}
      <span className="ct-ext" title="Lớp do DBpedia định nghĩa (rdfs:isDefinedBy dbo:); nhóm chỉ thêm nhãn tiếng Việt">
        DBpedia
      </span>
    </span>
  );
}

function ItemList({ items, more }: { items: TreeItem[]; more: string | null }) {
  if (items.length === 0) return null;
  return (
    <>
      <ul className="ct-inst">
        {items.map((it) => {
          const iri = it.iri || `${VRES_NS}${it.id}`;
          return (
            <li key={it.id}>
              <IriTip iri={iri}>
                <Link to={`/entity/${encodeURIComponent(it.id)}`} title={iri}>
                  {it.label}
                </Link>
              </IriTip>
            </li>
          );
        })}
      </ul>
      {more && <p className="ct-more">{more}</p>}
    </>
  );
}

function DirectList({ c, hasKids, filtering, ctl }: { c: TreeClass; hasKids: boolean; filtering: boolean; ctl: TreeCtl }) {
  const collapsible = c.directTotal > INST_COLLAPSE_MIN;
  const key = `${c.id}/inst`;
  // mặc định: đang lọc thì mở; nút có lớp con thì thu (đọc cây trước, tên sau), nút lá thì mở
  const def = filtering || !hasKids;
  const open = !collapsible || ctl.isOpen(key, def);
  const onToggle = () => ctl.toggle(key, def);
  const rest = c.directTotal - c.directShown; // directTotal đã tính sau lọc nên số dư chính xác
  return (
    <div className="ct-instwrap">
      <p className={`ct-direct${collapsible ? " ct-clickable" : ""}`} onClick={collapsible ? rowToggle(onToggle) : undefined}>
        {collapsible ? <Chevron small open={open} onToggle={onToggle} /> : <LeafMark small />}
        <span>Thực thể trực tiếp ({formatNumber(c.directTotal)})</span>
      </p>
      {open && <ItemList items={c.direct} more={rest > 0 ? `… và ${formatNumber(rest)} tài nguyên khác (dùng ô lọc để tìm)` : null} />}
    </div>
  );
}

interface ClassNodeProps {
  c: TreeClass;
  children: Map<string, TreeClass[]>;
  filtering: boolean;
  ancestors: Set<string>;
  target: string;
  ctl: TreeCtl;
}

function ClassNode({ c, children, filtering, ancestors, target, ctl }: ClassNodeProps) {
  const kids = children.get(c.id) ?? [];
  const hasInst = c.direct.length > 0;
  const expandable = kids.length > 0 || hasInst;
  // như Gradio: lớp gốc mở, lớp sâu hơn thu; đang lọc thì mở hết; thêm các lớp tổ tiên của deep link #Term
  const def = c.depth === 0 || filtering || ancestors.has(c.id);
  const open = expandable && ctl.isOpen(c.id, def);
  const onToggle = () => ctl.toggle(c.id, def);
  const inferredOnly = c.asserted === 0;
  return (
    <li className="ct-node" role="treeitem" aria-expanded={expandable ? open : undefined}>
      <div
        id={`cls-${c.term}`}
        className={`ct-row${expandable ? " ct-clickable" : ""}${c.term === target ? " ct-highlight" : ""}`}
        onClick={expandable ? rowToggle(onToggle) : undefined}
      >
        {expandable ? <Chevron open={open} onToggle={onToggle} /> : <LeafMark />}
        <span className="ct-text">
          <b>{c.label}</b> <TermLink id={c.id} term={c.term} />
          <DboChain c={c} />{" "}
          <span className="ct-count">{formatNumber(c.total)}</span>
          {inferredOnly ? (
            <>
              {" "}
              <span className="ct-badge" title="Không thực thể nào được khai báo trực tiếp thuộc lớp này; tất cả có lớp nhờ suy luận">
                suy luận
              </span>
            </>
          ) : (
            c.asserted < c.total && <span className="ct-muted"> ({formatNumber(c.asserted)} khai báo)</span>
          )}
        </span>
      </div>
      {open && (
        <div className="ct-children">
          {kids.length > 0 && (
            <ul className="ct-tree" role="group">
              {kids.map((k) => (
                <ClassNode key={k.id} c={k} children={children} filtering={filtering} ancestors={ancestors} target={target} ctl={ctl} />
              ))}
            </ul>
          )}
          {hasInst && <DirectList c={c} hasKids={kids.length > 0} filtering={filtering} ctl={ctl} />}
        </div>
      )}
    </li>
  );
}

function GroupNode({ g, filtering, ctl }: { g: TreeGroup; filtering: boolean; ctl: TreeCtl }) {
  const expandable = g.items.length > 0;
  const open = expandable && ctl.isOpen(g.id, filtering);
  const onToggle = () => ctl.toggle(g.id, filtering);
  // `matched` = số sau lọc (bằng `total` khi không lọc) nên số dư luôn chính xác
  const rest = g.matched - g.shown;
  const more = rest > 0 ? `… và ${formatNumber(rest)} tài nguyên khác (dùng ô lọc để tìm)` : null;
  return (
    <li className="ct-node" role="treeitem" aria-expanded={expandable ? open : undefined}>
      <div className={`ct-row${expandable ? " ct-clickable" : ""}`} onClick={expandable ? rowToggle(onToggle) : undefined}>
        {expandable ? <Chevron open={open} onToggle={onToggle} /> : <LeafMark />}
        <span className="ct-text">
          <b>{g.title}</b> <code className="ct-muted">{g.id}</code> <span className="ct-count">{formatNumber(g.total)}</span>{" "}
          <span className="ct-muted">{g.note}</span>
        </span>
      </div>
      {open && (
        <div className="ct-children">
          <ItemList items={g.items} more={more} />
        </div>
      )}
    </li>
  );
}

function Tree({ data, target }: { data: ResourceTree; target: string }) {
  const filtering = data.query.trim() !== "";
  const { roots, children } = useMemo(() => {
    const ids = new Set(data.classes.map((c) => c.id));
    const children = new Map<string, TreeClass[]>();
    const roots: TreeClass[] = [];
    for (const c of data.classes) {
      // giữ thứ tự máy chủ trả về; lớp cha không có trong danh sách (khi lọc) thì coi như gốc
      if (c.parent && ids.has(c.parent)) {
        const list = children.get(c.parent) ?? [];
        list.push(c);
        children.set(c.parent, list);
      } else roots.push(c);
    }
    return { roots, children };
  }, [data]);
  // deep link #Person: lớp đó và các lớp tổ tiên mặc định mở
  const ancestors = useMemo(() => {
    const out = new Set<string>();
    const byId = new Map(data.classes.map((c) => [c.id, c]));
    let cur = data.classes.find((c) => c.term === target);
    while (cur) {
      out.add(cur.id);
      cur = cur.parent ? byId.get(cur.parent) : undefined;
    }
    return out;
  }, [data, target]);

  // nút nào người dùng đã bấm thì ghi đè mặc định; đổi bộ lọc thì về mặc định (như Gradio vẽ lại cả cây)
  const [overrides, setOverrides] = useState<Record<string, boolean>>({});
  useEffect(() => setOverrides({}), [data.query]);
  const ctl = useMemo<TreeCtl>(
    () => ({
      isOpen: (key, def) => overrides[key] ?? def,
      toggle: (key, def) => setOverrides((o) => ({ ...o, [key]: !(o[key] ?? def) })),
    }),
    [overrides],
  );
  const setAll = (open: boolean) => {
    const o: Record<string, boolean> = {};
    for (const c of data.classes) {
      o[c.id] = open;
      if (!open) o[`${c.id}/inst`] = false; // "Mở tất cả" để danh sách tên theo mặc định cho khỏi quá dài
    }
    for (const g of data.groups) o[g.id] = open;
    setOverrides(o);
  };

  if (data.classes.length === 0 && data.groups.length === 0) {
    return <p className="ct-empty">Không có tài nguyên nào có tên chứa “{data.query}”.</p>;
  }
  return (
    <>
      <p className="ct-sum">
        {formatNumber(data.summary.classes)} lớp <code>vio:</code>, lớp cha DBpedia (<code>dbo:</code>) ghi sau dấu ⊑ ·{" "}
        {formatNumber(data.summary.resources)} tài nguyên <code>vres:</code>. Số bên cạnh
        lớp là số thực thể của lớp và các lớp con (gồm cả thực thể có lớp nhờ suy luận); danh sách tên chỉ gồm thực thể <b>trực tiếp</b> của lớp
        đó.
      </p>
      <div className="ct-toolbar">
        <button type="button" className="btn" onClick={() => setAll(true)}>
          Mở tất cả
        </button>
        <button type="button" className="btn" onClick={() => setAll(false)}>
          Thu tất cả
        </button>
      </div>
      <ul className="ct-tree" role="tree" aria-label="Cây tài nguyên theo lớp">
        {roots.map((c) => (
          <ClassNode key={c.id} c={c} children={children} filtering={filtering} ancestors={ancestors} target={target} ctl={ctl} />
        ))}
        {data.groups.map((g) => (
          <GroupNode key={g.id} g={g} filtering={filtering} ctl={ctl} />
        ))}
      </ul>
    </>
  );
}

// ============================================================================
// Thuộc tính và tiên đề OWL (/api/ontology), chỉ nạp khi mở <details>
// ============================================================================

function Inferred({ n, title = "số triple do bộ suy luận OWL 2 RL thêm vào nhờ định nghĩa này" }: { n: number; title?: string }) {
  if (n <= 0) return null;
  return (
    <span className="onto-badge inf" title={title}>
      +{formatNumber(n)} suy luận
    </span>
  );
}

/** `anchor`: dòng đầu tiên của thuộc tính này (một thuộc tính hiện một lần cho mỗi lớp domain) mang id cho deep link #term. */
function PropertyRow({ p, anchor, target }: { p: OntologyProperty; anchor: boolean; target: string }) {
  return (
    <li id={anchor ? `prop-${p.term}` : undefined} className={`onto-prop${p.term === target ? " highlight" : ""}`}>
      <TermLink id={p.id} term={p.term} />
      <span className="onto-arrow">→</span>
      <code className="muted">{p.range ?? "?"}</code>
      <span className="onto-plabel">{p.label}</span>
      {p.subPropertyOf.map((s) => (
        <span key={s} className="onto-badge" title="rdfs:subPropertyOf">
          ⊑ {s}
        </span>
      ))}
      {p.functional && (
        <span className="onto-badge" title="owl:FunctionalProperty: mỗi chủ thể chỉ có một giá trị">
          functional
        </span>
      )}
      {p.inverseOf && (
        <span className="onto-badge" title="owl:inverseOf">
          nghịch đảo của {p.inverseOf}
        </span>
      )}
      <Inferred n={p.inferred} />
    </li>
  );
}

function ClassProperties({ c, anchors, target }: { c: OntologyClass; anchors: Map<string, string>; target: string }) {
  const inferred = c.total - c.asserted;
  return (
    <li className="onto-class" style={{ marginLeft: c.depth * 18 }}>
      <div className="onto-class-head">
        <strong>{c.label}</strong>
        <TermLink id={c.id} term={c.term} />
        {c.dbo.length > 0 && <span className="onto-sub">⊑ {[c.dbo.join(", "), ...c.dboUp].join(" ⊑ ")}</span>}
        <span className="onto-count" title={`${formatNumber(c.asserted)} thực thể khai báo · ${formatNumber(c.total)} sau suy luận`}>
          {formatNumber(c.asserted)} / {inferred > 0 ? <span className="onto-inferred">{formatNumber(c.total)}</span> : formatNumber(c.total)}
        </span>
      </div>
      {c.properties.length > 0 ? (
        <ul className="onto-props">
          {c.properties.map((p) => (
            <PropertyRow key={p.id} p={p} anchor={anchors.get(p.term) === c.id} target={target} />
          ))}
        </ul>
      ) : (
        <p className="muted small onto-none">Không có thuộc tính riêng (kế thừa từ lớp cha).</p>
      )}
    </li>
  );
}

function Axioms({ axioms }: { axioms: Ontology["axioms"] }) {
  return (
    <>
      <h4>Chuỗi thuộc tính</h4>
      {axioms.chains.length === 0 && <p className="muted small">Không có.</p>}
      <ul>
        {axioms.chains.map((ch) => (
          <li key={ch.property}>
            <span className="onto-formula">
              {ch.chain.map(local).join(" ∘ ")} ⊑ {local(ch.property)}
            </span>
            <Inferred n={ch.inferred} />
          </li>
        ))}
      </ul>

      <h4>Nghịch đảo</h4>
      {axioms.inverses.length === 0 && <p className="muted small">Không có.</p>}
      <ul>
        {axioms.inverses.map((inv) => (
          <li key={`${inv.a}|${inv.b}`}>
            <span className="onto-formula">
              {local(inv.a)} ≡ {local(inv.b)}⁻
            </span>
            <Inferred n={inv.inferredA} title={`triple ${inv.a} suy ra từ ${inv.b}`} />
            <Inferred n={inv.inferredB} title={`triple ${inv.b} suy ra từ ${inv.a}`} />
          </li>
        ))}
      </ul>

      <h4>Ràng buộc</h4>
      {axioms.restrictions.length === 0 && <p className="muted small">Không có.</p>}
      <ul>
        {axioms.restrictions.map((r) => (
          <li key={`${r.onClass}|${r.property}|${r.filler}`}>
            <span className="onto-formula" title={`${r.kind} · ${r.onClass} · ${r.property} · ${r.filler}`}>
              {r.text}
            </span>
            <Inferred n={r.inferred} />
          </li>
        ))}
      </ul>

      <h4>Rời nhau</h4>
      {axioms.disjoint.length === 0 && <p className="muted small">Không có.</p>}
      <ul>
        {axioms.disjoint.map((group) => (
          <li key={group.join("|")} className="onto-disjoint">
            <span className="muted small">owl:AllDisjointClasses</span>
            {group.map((cls) => (
              <span key={cls} className="chip">
                {cls}
              </span>
            ))}
          </li>
        ))}
      </ul>
    </>
  );
}

function owlError(error: string): string {
  return `${error}${error.includes("404") ? " Máy chủ này chưa có endpoint /api/ontology." : ""}`;
}

/** Cột phải (dính dưới thanh điều hướng): tiên đề OWL kèm số triple suy ra, số liệu gọn, tải ontology, ví dụ curl. */
function AxiomsCard({ owl }: { owl: ApiState<Ontology> }) {
  const curl = `curl -H "Accept: text/turtle" ${window.location.origin}/ontology/playedFor`;
  const stats = owl.data?.stats;
  return (
    <aside className="card onto-sticky onto-axioms">
      <h2>Tiên đề OWL 2 RL</h2>
      <p className="muted small">Các định nghĩa OWL khiến bộ suy luận thêm triple; số tím là triple suy ra được từ từng tiên đề.</p>
      {owl.loading && <Loading text="Đang tải ontology…" />}
      {owl.error && <ErrorState message={owlError(owl.error)} />}
      {owl.data && stats && (
        <>
          <Axioms axioms={owl.data.axioms} />
          <p className="onto-foot small muted">
            {formatNumber(stats.classes)} lớp · {formatNumber(stats.objectProperties)} thuộc tính đối tượng ·{" "}
            {formatNumber(stats.datatypeProperties)} thuộc tính dữ liệu · {formatNumber(stats.triples)} triple ·{" "}
            <a href={stats.download} target="_blank" rel="noopener noreferrer">
              Tải vi-ontology.ttl
            </a>
          </p>
          <pre className="curl onto-curl">{curl}</pre>
        </>
      )}
    </aside>
  );
}

/** Nội dung details "Thuộc tính theo lớp": thuộc tính theo từng lớp + thuộc tính không có domain. */
function ClassPropsSection({ data, target }: { data: Ontology; target: string }) {
  const noDomain = data.properties.filter((p) => !p.domain);
  // term → lớp chứa dòng đầu tiên của thuộc tính ("" = mục không có domain): chỉ dòng đó mang id prop-{term}
  const anchors = useMemo(() => {
    const out = new Map<string, string>();
    for (const c of data.classes) for (const p of c.properties) if (!out.has(p.term)) out.set(p.term, c.id);
    for (const p of data.properties) if (!p.domain && !out.has(p.term)) out.set(p.term, "");
    return out;
  }, [data]);
  return (
    <div className="onto-owl">
      <p className="muted small">Số bên phải: thực thể khai báo / sau suy luận. Bấm mã lớp hoặc thuộc tính để mở định nghĩa (tab mới).</p>
      <ul className="onto-tree">
        {data.classes.map((c) => (
          <ClassProperties key={c.id} c={c} anchors={anchors} target={target} />
        ))}
      </ul>
      <h4 className="onto-h4">Thuộc tính không có domain ({noDomain.length})</h4>
      <p className="muted small">Dùng chung cho nhiều lớp nên không gắn rdfs:domain; bộ suy luận không suy ra lớp của chủ thể từ chúng.</p>
      {noDomain.length === 0 ? (
        <p className="muted small">Mọi thuộc tính đều có domain.</p>
      ) : (
        <ul className="onto-props onto-nodomain">
          {noDomain.map((p) => (
            <PropertyRow key={p.id} p={p} anchor={anchors.get(p.term) === ""} target={target} />
          ))}
        </ul>
      )}
    </div>
  );
}

// ============================================================================
// Trang
// ============================================================================

/** Ontology vio: trái = cây tài nguyên (giống tab "Cây tài nguyên" của Gradio) + thuộc tính theo lớp thu gọn; phải = tiên đề OWL. */
export function OntologyPage() {
  const [params, setParams] = useSearchParams();
  const urlQ = params.get("q") ?? "";
  const [input, setInput] = useState(urlQ);
  const { hash } = useLocation();
  const target = hash ? decodeURIComponent(hash.slice(1)) : "";

  // ô lọc → URL ?q= sau 250 ms (URL là nguồn sự thật để chia sẻ / nút Back)
  useEffect(() => {
    const t = window.setTimeout(() => {
      const q = input.trim();
      if (q !== urlQ) setParams(q ? { q } : {}, { replace: true });
    }, FILTER_DEBOUNCE_MS);
    return () => window.clearTimeout(t);
  }, [input, urlQ, setParams]);
  // nút Back / link có ?q= đổi URL: đồng bộ lại ô nhập
  useEffect(() => {
    setInput((cur) => (cur.trim() === urlQ ? cur : urlQ));
  }, [urlQ]);

  const tree = useApi<ResourceTree>(`/api/tree${urlQ ? `?q=${encodeURIComponent(urlQ)}` : ""}`);
  const owl = useApi<Ontology>("/api/ontology"); // cột tiên đề hiện ngay nên nạp ngay

  // deep link #Person: cuộn tới dòng lớp trong cây (các lớp tổ tiên đã được mở)
  useEffect(() => {
    if (!tree.data || !target) return;
    document.getElementById(`cls-${target}`)?.scrollIntoView({ block: "center" });
  }, [tree.data, target]);

  // deep link #playedFor (thuộc tính, không phải lớp): mở "Thuộc tính theo lớp", cuộn tới dòng đầu tiên và tô mọi dòng của nó
  const [propsOpen, setPropsOpen] = useState(false);
  const isProp = useMemo(() => {
    const o = owl.data;
    if (!o || !target || o.classes.some((c) => c.term === target)) return false;
    return o.properties.some((p) => p.term === target) || o.classes.some((c) => c.properties.some((p) => p.term === target));
  }, [owl.data, target]);
  useEffect(() => {
    if (isProp) setPropsOpen(true);
  }, [isProp, target]);
  const treeReady = tree.data !== null; // cây tải xong đẩy details xuống: cuộn lại một lần
  useEffect(() => {
    if (!propsOpen || !isProp) return;
    document.getElementById(`prop-${target}`)?.scrollIntoView({ block: "center" });
  }, [propsOpen, isProp, target, treeReady]);

  const propCount = owl.data ? owl.data.stats.objectProperties + owl.data.stats.datatypeProperties : null;

  return (
    <div className="ontology">
      <h1 className="page-title">Cây tài nguyên</h1>
      <p className="muted lead">
        Duyệt mọi tài nguyên <code>vres:</code> theo cây lớp <code>vio:</code>; mỗi lớp ghi lớp cha DBpedia sau dấu ⊑, gốc ghi cả
        chuỗi (<code>vio:Person ⊑ dbo:Person ⊑ dbo:Animal</code>). Bấm tên để mở trang thực thể.
      </p>

      <div className="onto-layout">
        <div className="onto-main">
          <section className="card ct">
            <div className="ct-filter">
              <label htmlFor="ct-q">Lọc theo tên</label>
              <input
                id="ct-q"
                type="search"
                value={input}
                placeholder="ví dụ: hoàng anh, hoang anh"
                autoComplete="off"
                onChange={(e) => setInput(e.target.value)}
              />
              {tree.loading && tree.data && <span className="ct-loading">Đang lọc…</span>}
            </div>
            {tree.loading && !tree.data && <Loading text="Đang tải cây tài nguyên…" />}
            {tree.error && <ErrorState message={`${tree.error}${tree.error.includes("404") ? " Máy chủ này chưa có endpoint /api/tree." : ""}`} />}
            {tree.data && <Tree data={tree.data} target={target} />}
          </section>

          <details className="card ct-owl" open={propsOpen} onToggle={(e) => setPropsOpen(e.currentTarget.open)}>
            <summary>Thuộc tính theo lớp{propCount !== null && ` (${formatNumber(propCount)} thuộc tính)`}</summary>
            {owl.loading && <Loading text="Đang tải ontology…" />}
            {owl.error && <ErrorState message={owlError(owl.error)} />}
            {owl.data && <ClassPropsSection data={owl.data} target={target} />}
          </details>
        </div>

        <AxiomsCard owl={owl} />
      </div>
    </div>
  );
}
