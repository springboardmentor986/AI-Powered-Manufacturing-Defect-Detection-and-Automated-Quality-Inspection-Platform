import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import Sidebar from "../components/Sidebar";
import {
  getToken,
  clearToken,
  getCurrentUser,
  listImages,
  uploadImage,
  getImageFileUrl,
} from "../lib/api";

const PAGE_SIZE = 12;

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [images, setImages] = useState([]);
  const [categoryId, setCategoryId] = useState("1");
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [loadingPage, setLoadingPage] = useState(true);
  const [page, setPage] = useState(1);
  const [filterCategory, setFilterCategory] = useState("all");

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    (async () => {
      try {
        const [me, imgs] = await Promise.all([getCurrentUser(), listImages()]);
        setUser(me);
        setImages(imgs.reverse());
      } catch (err) {
        clearToken();
        router.push("/login");
      } finally {
        setLoadingPage(false);
      }
    })();
  }, [router]);

  const stats = useMemo(() => {
    const categories = new Set(images.map((i) => i.category_id).filter(Boolean));
    const mvtec = images.filter((i) => i.image_source === "mvtec").length;
    const uploaded = images.length - mvtec;
    return {
      total: images.length,
      categories: categories.size,
      mvtec,
      uploaded,
    };
  }, [images]);

  const categoryOptions = useMemo(() => {
    const ids = Array.from(
      new Set(images.map((i) => i.category_id).filter(Boolean))
    ).sort((a, b) => a - b);
    return ids;
  }, [images]);

  const filteredImages = useMemo(() => {
    if (filterCategory === "all") return images;
    return images.filter((i) => String(i.category_id) === String(filterCategory));
  }, [images, filterCategory]);

  const totalPages = Math.max(1, Math.ceil(filteredImages.length / PAGE_SIZE));
  const pageImages = filteredImages.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE
  );

  useEffect(() => {
    setPage(1);
  }, [filterCategory]);

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) {
      setError("Choose an image file first.");
      return;
    }
    setError("");
    setStatus("");
    setUploading(true);
    try {
      await uploadImage({ categoryId, file });
      setStatus("Image uploaded — queued for inspection.");
      setFile(null);
      setFileName("");
      e.target.reset();
      const imgs = await listImages();
      setImages(imgs.reverse());
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  if (loadingPage) {
    return (
      <div style={styles.page}>
        <div style={styles.bootScreen}>
          <div style={styles.bootPulse} />
          <p style={styles.bootText}>Initializing inspection dashboard…</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.shell}>
      <Sidebar />
      <div style={styles.page}>
        <div style={styles.bgGrid} />

        <header style={styles.header}>
          <div>
            <div style={styles.eyebrow}>VISIONINSPECT AI · CONTROL ROOM</div>
            <h1 style={styles.title}>Inspection Dashboard</h1>
          </div>
          <div style={styles.headerRight}>
            {user && (
              <div style={styles.userBadge}>
                <span style={styles.userDot} />
                <div>
                  <div style={styles.userName}>{user.name}</div>
                  <div style={styles.userRole}>{user.role}</div>
                </div>
              </div>
            )}
            <button onClick={handleLogout} style={styles.logoutButton}>
              Sign out
            </button>
          </div>
        </header>

        <main style={styles.main}>
          {/* STAT STRIP */}
          <section style={styles.statRow}>
            <StatCard label="Units logged" value={stats.total} accent="var(--accent)" />
            <StatCard label="Categories" value={stats.categories} accent="#7dd3fc" />
            <StatCard label="MVTec dataset" value={stats.mvtec} accent="#3dd68c" />
            <StatCard label="Manually uploaded" value={stats.uploaded} accent="#c084fc" />
          </section>

          {/* SCAN BAY — full width, horizontal layout */}
          <section style={styles.uploadCard}>
            <div style={styles.uploadCardInner}>
              <div style={styles.uploadIntro}>
                <div style={styles.cardHeaderRow}>
                  <h2 style={styles.cardTitle}>Scan bay</h2>
                  <span style={styles.liveDot} />
                </div>
                <p style={styles.cardSubtitle}>
                  Submit a product image for defect detection and quality
                  review.
                </p>
              </div>

              <form onSubmit={handleUpload} style={styles.formRow}>
                <label style={styles.labelCompact}>
                  Category ID
                  <input
                    type="number"
                    min="1"
                    required
                    value={categoryId}
                    onChange={(e) => setCategoryId(e.target.value)}
                    style={styles.input}
                  />
                </label>

                <label htmlFor="fileInput" style={styles.dropZoneCompact}>
                  <input
                    id="fileInput"
                    type="file"
                    accept="image/*"
                    required
                    onChange={(e) => {
                      const f = e.target.files[0];
                      setFile(f);
                      setFileName(f ? f.name : "");
                    }}
                    style={styles.hiddenFileInput}
                  />
                  <span style={styles.dropIconSmall}>⤒</span>
                  <span style={styles.dropTextCompact}>
                    {fileName || "Click to select an image"}
                  </span>
                </label>

                <button type="submit" disabled={uploading} style={styles.button}>
                  {uploading ? "Uploading…" : "Upload for inspection"}
                </button>
              </form>
            </div>
            {error && <div style={styles.error}>{error}</div>}
            {status && <div style={styles.success}>{status}</div>}
          </section>

          {/* RECENT UPLOADS */}
          <section style={styles.listSection}>
            <div style={styles.listHeader}>
              <h2 style={styles.cardTitle}>
                Recent units{" "}
                <span style={styles.countBadge}>{filteredImages.length}</span>
              </h2>
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                style={styles.filterSelect}
              >
                <option value="all">All categories</option>
                {categoryOptions.map((id) => (
                  <option key={id} value={id}>
                    Category {id}
                  </option>
                ))}
              </select>
            </div>

            {pageImages.length === 0 ? (
              <div style={styles.emptyState}>
                No images uploaded yet. Upload one to start an inspection.
              </div>
            ) : (
              <div style={styles.cardGrid}>
                {pageImages.map((img) => (
                  <Link
                    href={`/inspect/${img.image_id}`}
                    key={img.image_id}
                    style={styles.unitCard}
                  >
                    <div style={styles.thumbWrap}>
                      <img
                        src={getImageFileUrl(img.image_id)}
                        alt={`Unit ${img.image_id}`}
                        style={styles.thumb}
                        loading="lazy"
                      />
                      <span style={styles.thumbId}>#{img.image_id}</span>
                      <span
                        style={{
                          ...styles.sourceTag,
                          color:
                            img.image_source === "mvtec"
                              ? "#3dd68c"
                              : "var(--accent)",
                          borderColor:
                            img.image_source === "mvtec"
                              ? "#3dd68c"
                              : "var(--accent)",
                        }}
                      >
                        {img.image_source}
                      </span>
                    </div>
                    <div style={styles.unitMeta}>
                      <span style={styles.unitCategory}>
                        Category {img.category_id ?? "—"}
                      </span>
                      <span style={styles.unitArrow}>Inspect →</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}

            {totalPages > 1 && (
              <div style={styles.pagination}>
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  style={styles.pageButton}
                >
                  ← Prev
                </button>
                <span style={styles.pageLabel}>
                  Page <span style={styles.mono}>{page}</span> /{" "}
                  <span style={styles.mono}>{totalPages}</span>
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  style={styles.pageButton}
                >
                  Next →
                </button>
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

function StatCard({ label, value, accent }) {
  return (
    <div style={styles.statCard}>
      <div style={{ ...styles.statAccent, background: accent }} />
      <div style={styles.statValue}>{value.toLocaleString()}</div>
      <div style={styles.statLabel}>{label}</div>
    </div>
  );
}

const styles = {
  shell: {
    display: "flex",
    minHeight: "100vh",
  },
  page: {
    flex: 1,
    minHeight: "100vh",
    padding: "0 0 48px",
    position: "relative",
    overflow: "hidden",
  },
  bgGrid: {
    position: "fixed",
    inset: 0,
    backgroundImage:
      "linear-gradient(var(--border) 1px, transparent 1px), linear-gradient(90deg, var(--border) 1px, transparent 1px)",
    backgroundSize: "48px 48px",
    opacity: 0.15,
    pointerEvents: "none",
    zIndex: 0,
  },
  bootScreen: {
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 16,
  },
  bootPulse: {
    width: 14,
    height: 14,
    borderRadius: "50%",
    background: "var(--accent)",
    boxShadow: "0 0 0 0 rgba(245,166,35,0.6)",
    animation: "pulse 1.8s ease-out infinite",
  },
  bootText: {
    color: "var(--text-muted)",
    fontFamily: "var(--font-mono)",
    fontSize: 13,
  },
  header: {
    position: "relative",
    zIndex: 1,
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "24px 32px",
    borderBottom: "1px solid var(--border)",
  },
  eyebrow: {
    fontFamily: "var(--font-mono)",
    fontSize: 11,
    letterSpacing: "0.14em",
    color: "var(--accent)",
  },
  title: {
    fontFamily: "var(--font-display)",
    fontSize: 24,
    margin: "4px 0 0",
  },
  headerRight: {
    display: "flex",
    alignItems: "center",
    gap: 16,
  },
  userBadge: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  userDot: {
    width: 8,
    height: 8,
    borderRadius: "50%",
    background: "var(--ok)",
    boxShadow: "0 0 8px var(--ok)",
  },
  userName: {
    fontSize: 14,
    fontWeight: 600,
  },
  userRole: {
    fontSize: 11,
    color: "var(--text-muted)",
    fontFamily: "var(--font-mono)",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
  },
  logoutButton: {
    background: "transparent",
    border: "1px solid var(--border)",
    color: "var(--text)",
    borderRadius: 8,
    padding: "8px 14px",
    fontSize: 13,
    cursor: "pointer",
  },
  main: {
    position: "relative",
    zIndex: 1,
    maxWidth: 1200,
    margin: "0 auto",
    padding: "32px",
    display: "flex",
    flexDirection: "column",
    gap: 24,
  },
  statRow: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 16,
  },
  statCard: {
    position: "relative",
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 12,
    padding: "18px 20px",
    overflow: "hidden",
  },
  statAccent: {
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: 3,
  },
  statValue: {
    fontFamily: "var(--font-display)",
    fontSize: 28,
    fontWeight: 700,
  },
  statLabel: {
    fontSize: 12,
    color: "var(--text-muted)",
    marginTop: 4,
  },
  uploadCard: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 12,
    padding: "20px 24px",
  },
  uploadCardInner: {
    display: "flex",
    alignItems: "center",
    gap: 28,
    flexWrap: "wrap",
  },
  uploadIntro: {
    minWidth: 220,
  },
  cardHeaderRow: {
    display: "flex",
    alignItems: "center",
    gap: 10,
  },
  liveDot: {
    width: 8,
    height: 8,
    borderRadius: "50%",
    background: "var(--accent)",
    boxShadow: "0 0 8px var(--accent)",
    animation: "pulse 1.8s ease-out infinite",
  },
  cardTitle: {
    fontFamily: "var(--font-display)",
    fontSize: 18,
    margin: 0,
    display: "flex",
    alignItems: "center",
    gap: 10,
  },
  cardSubtitle: {
    color: "var(--text-muted)",
    fontSize: 13,
    margin: "4px 0 0",
    maxWidth: 260,
  },
  formRow: {
    display: "flex",
    alignItems: "center",
    gap: 14,
    flex: 1,
    flexWrap: "wrap",
  },
  labelCompact: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
    fontSize: 12,
    color: "var(--text-muted)",
    width: 110,
  },
  input: {
    background: "var(--surface-2)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    padding: "10px 12px",
    color: "var(--text)",
    fontSize: 14,
  },
  dropZoneCompact: {
    position: "relative",
    display: "flex",
    alignItems: "center",
    gap: 10,
    border: "1.5px dashed var(--border)",
    borderRadius: 10,
    padding: "12px 18px",
    cursor: "pointer",
    background: "var(--surface-2)",
    flex: 1,
    minWidth: 220,
  },
  hiddenFileInput: {
    position: "absolute",
    inset: 0,
    opacity: 0,
    cursor: "pointer",
  },
  dropIconSmall: {
    fontSize: 16,
    color: "var(--accent)",
    transform: "rotate(45deg)",
  },
  dropTextCompact: {
    fontSize: 12,
    color: "var(--text-muted)",
    fontFamily: "var(--font-mono)",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  button: {
    background: "var(--accent)",
    color: "#14161a",
    border: "none",
    borderRadius: 8,
    padding: "12px 20px",
    fontWeight: 600,
    fontSize: 14,
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
  error: {
    background: "rgba(255,92,92,0.1)",
    border: "1px solid var(--danger)",
    color: "var(--danger)",
    padding: "10px 12px",
    borderRadius: 8,
    fontSize: 13,
    marginTop: 14,
  },
  success: {
    background: "rgba(61,214,140,0.1)",
    border: "1px solid var(--ok)",
    color: "var(--ok)",
    padding: "10px 12px",
    borderRadius: 8,
    fontSize: 13,
    marginTop: 14,
  },
  listSection: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 12,
    padding: "24px",
  },
  listHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 18,
    flexWrap: "wrap",
    gap: 12,
  },
  countBadge: {
    fontFamily: "var(--font-mono)",
    fontSize: 12,
    color: "var(--accent)",
    border: "1px solid var(--accent-dim)",
    borderRadius: 6,
    padding: "1px 8px",
  },
  filterSelect: {
    background: "var(--surface-2)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    padding: "8px 10px",
    color: "var(--text)",
    fontSize: 13,
  },
  emptyState: {
    color: "var(--text-muted)",
    fontSize: 14,
    padding: "24px",
    textAlign: "center",
    border: "1px dashed var(--border)",
    borderRadius: 8,
  },
  cardGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))",
    gap: 14,
  },
  unitCard: {
    textDecoration: "none",
    color: "var(--text)",
    background: "var(--surface-2)",
    border: "1px solid var(--border)",
    borderRadius: 10,
    overflow: "hidden",
    display: "block",
    transition: "border-color 0.15s ease, transform 0.15s ease",
  },
  thumbWrap: {
    position: "relative",
    aspectRatio: "1 / 1",
    background: "#0b0d10",
  },
  thumb: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
  },
  thumbId: {
    position: "absolute",
    top: 6,
    left: 6,
    fontFamily: "var(--font-mono)",
    fontSize: 10,
    background: "rgba(0,0,0,0.6)",
    padding: "2px 6px",
    borderRadius: 4,
  },
  sourceTag: {
    position: "absolute",
    bottom: 6,
    right: 6,
    fontFamily: "var(--font-mono)",
    fontSize: 9,
    letterSpacing: "0.06em",
    textTransform: "uppercase",
    border: "1px solid",
    borderRadius: 20,
    padding: "2px 8px",
    background: "rgba(0,0,0,0.6)",
  },
  unitMeta: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "8px 10px",
    fontSize: 11,
  },
  unitCategory: {
    color: "var(--text-muted)",
  },
  unitArrow: {
    color: "var(--accent)",
    fontFamily: "var(--font-mono)",
  },
  pagination: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    gap: 16,
    marginTop: 20,
  },
  pageButton: {
    background: "var(--surface-2)",
    border: "1px solid var(--border)",
    color: "var(--text)",
    borderRadius: 8,
    padding: "8px 14px",
    fontSize: 13,
    cursor: "pointer",
  },
  pageLabel: {
    fontSize: 13,
    color: "var(--text-muted)",
  },
  mono: {
    fontFamily: "var(--font-mono)",
    color: "var(--text)",
  },
};
