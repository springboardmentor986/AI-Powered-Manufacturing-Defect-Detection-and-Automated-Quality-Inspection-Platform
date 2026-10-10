import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import Sidebar from "../components/Sidebar";
import { getToken, getImages, getCategories } from "../lib/api";
import { ui, badge, downloadCsv } from "../lib/ui";

const PAGE_SIZE = 25;

function statusInfo(s) {
  if (s === "normal") return { label: "PASS", color: "#3dd68c" };
  if (s === "defective") return { label: "FAIL", color: "#ff5c5c" };
  return { label: "PENDING", color: "#8a94a1" };
}

function defectLabel(img) {
  if (img.inspection_status !== "defective") return "-";
  if (img.image_type && img.image_type.startsWith("test_defect:")) {
    return img.image_type.split(":")[1].replace(/_/g, " ");
  }
  return "anomaly";
}

function formatDate(v) {
  const d = new Date(v);
  return isNaN(d.getTime()) ? "-" : d.toLocaleDateString();
}

export default function Inspections() {
  const router = useRouter();
  const [images, setImages] = useState([]);
  const [categories, setCategories] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [fStatus, setFStatus] = useState("all");
  const [fCategory, setFCategory] = useState("all");
  const [fSource, setFSource] = useState("all");
  const [page, setPage] = useState(0);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    (async () => {
      try {
        setImages(await getImages());
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
      try {
        const cats = await getCategories();
        const map = {};
        cats.forEach((c) => {
          map[c.category_id] = c.category_name;
        });
        setCategories(map);
      } catch (e) {
        /* fall back to Category <id> */
      }
    })();
  }, [router]);

  const catName = (id) => categories[id] || "Category " + id;

  const categoryIds = useMemo(
    () => Array.from(new Set(images.map((i) => i.category_id))).sort((a, b) => a - b),
    [images]
  );

  const filtered = useMemo(
    () =>
      images
        .filter((img) => {
          const st = img.inspection_status || "pending";
          if (fStatus !== "all" && st !== fStatus) return false;
          if (fCategory !== "all" && String(img.category_id) !== fCategory) return false;
          if (fSource !== "all" && img.image_source !== fSource) return false;
          return true;
        })
        .sort((a, b) => b.image_id - a.image_id),
    [images, fStatus, fCategory, fSource]
  );

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const visible = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const changeFilter = (setter) => (e) => {
    setter(e.target.value);
    setPage(0);
  };

  const exportCsv = () => {
    downloadCsv(
      "inspections_" + new Date().toISOString().slice(0, 10) + ".csv",
      ["unit_id", "category", "source", "defect", "result", "logged"],
      filtered.map((img) => [
        img.image_id,
        catName(img.category_id),
        img.image_source,
        defectLabel(img),
        statusInfo(img.inspection_status).label,
        formatDate(img.created_at),
      ])
    );
  };

  return (
    <div style={ui.shell}>
      <Sidebar />
      <div style={ui.page}>
        <header style={ui.header}>
          <div>
            <div style={ui.eyebrow}>VISIONINSPECT AI - INSPECTIONS</div>
            <h1 style={ui.title}>All Inspections</h1>
            <div style={ui.subtitle}>
              {images.length} units logged. Click a row to open its result.
            </div>
          </div>
          <button style={ui.button} onClick={exportCsv} disabled={!filtered.length}>
            Export CSV
          </button>
        </header>

        <section style={ui.panel}>
          <div style={ui.row}>
            <select style={ui.select} value={fStatus} onChange={changeFilter(setFStatus)}>
              <option value="all">All results</option>
              <option value="defective">Fail</option>
              <option value="normal">Pass</option>
              <option value="pending">Pending</option>
            </select>
            <select style={ui.select} value={fCategory} onChange={changeFilter(setFCategory)}>
              <option value="all">All categories</option>
              {categoryIds.map((id) => (
                <option key={id} value={String(id)}>
                  {catName(id)}
                </option>
              ))}
            </select>
            <select style={ui.select} value={fSource} onChange={changeFilter(setFSource)}>
              <option value="all">All sources</option>
              <option value="mvtec">MVTec dataset</option>
              <option value="uploaded">Uploaded</option>
            </select>
          </div>
        </section>

        {loading && <div style={ui.msg}>Loading inspections...</div>}
        {error && <div style={ui.msg}>Error: {error}</div>}

        {!loading && !error && (
          <section style={ui.panel}>
            <div style={ui.tableWrap}>
              <table style={ui.table}>
                <thead>
                  <tr>
                    <th style={ui.th}>Unit</th>
                    <th style={ui.th}>Category</th>
                    <th style={ui.th}>Source</th>
                    <th style={ui.th}>Defect</th>
                    <th style={ui.th}>Result</th>
                    <th style={ui.th}>Logged</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map((img) => {
                    const st = statusInfo(img.inspection_status);
                    return (
                      <tr
                        key={img.image_id}
                        style={{ cursor: "pointer" }}
                        onClick={() => router.push("/inspect/" + img.image_id)}
                      >
                        <td style={ui.td}>#{img.image_id}</td>
                        <td style={ui.td}>{catName(img.category_id)}</td>
                        <td style={ui.td}>{img.image_source}</td>
                        <td style={ui.td}>{defectLabel(img)}</td>
                        <td style={ui.td}>
                          <span style={badge(st.color)}>{st.label}</span>
                        </td>
                        <td style={ui.td}>{formatDate(img.created_at)}</td>
                      </tr>
                    );
                  })}
                  {!visible.length && (
                    <tr>
                      <td style={ui.td} colSpan={6}>
                        No units match these filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div style={ui.pager}>
              <span>
                {filtered.length} of {images.length} units - page {page + 1} of {pageCount}
              </span>
              <div style={ui.row}>
                <button
                  style={ui.buttonGhost}
                  disabled={page === 0}
                  onClick={() => setPage(page - 1)}
                >
                  Prev
                </button>
                <button
                  style={ui.buttonGhost}
                  disabled={page >= pageCount - 1}
                  onClick={() => setPage(page + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}