import { FormEvent, useEffect, useMemo, useState } from "react";
import { BrowserRouter, Navigate, NavLink, Route, Routes } from "react-router-dom";
import {
  ApiError,
  getConfig,
  getScreenshot,
  getScreenshotImageUrl,
  listScreenshots,
  listSummaries,
  updateConfig,
} from "./api";
import type { ScreenshotItem, SummaryItem } from "./types";

const navItems = [
  { to: "/screenshots", label: "截图浏览" },
  { to: "/config", label: "配置编辑" },
  { to: "/summaries", label: "摘要查询" },
];

function formatDefaultDate(hoursOffset: number): string {
  const value = new Date(Date.now() + hoursOffset * 60 * 60 * 1000);
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, "0")}-${String(value.getDate()).padStart(2, "0")}T${String(value.getHours()).padStart(2, "0")}:${String(value.getMinutes()).padStart(2, "0")}`;
}

function formatTime(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}

function AppShell() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-100 via-emerald-50 to-cyan-100 p-4 text-slate-900 sm:p-8">
      <section className="mx-auto max-w-6xl rounded-2xl border border-white/70 bg-white/85 p-5 shadow-xl backdrop-blur sm:p-8">
        <header className="mb-6 flex flex-col gap-3 border-b border-slate-200 pb-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-slate-800">Recall Frontend MVP</h1>
            <p className="text-sm text-slate-600">截图查询、配置编辑与摘要浏览</p>
          </div>
          <nav className="flex flex-wrap gap-2">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded-full px-4 py-2 text-sm font-medium transition ${
                    isActive
                      ? "bg-slate-900 text-white"
                      : "border border-slate-300 bg-white text-slate-700 hover:border-slate-400"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </header>

        <Routes>
          <Route path="/screenshots" element={<ScreenshotsPage />} />
          <Route path="/config" element={<ConfigPage />} />
          <Route path="/summaries" element={<SummariesPage />} />
          <Route path="*" element={<Navigate to="/screenshots" replace />} />
        </Routes>
      </section>
    </main>
  );
}

function ScreenshotsPage() {
  const [startTime, setStartTime] = useState(() => formatDefaultDate(-24));
  const [endTime, setEndTime] = useState(() => formatDefaultDate(0));
  const [limit, setLimit] = useState(50);
  const [items, setItems] = useState<ScreenshotItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectedDetail, setSelectedDetail] = useState<ScreenshotItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const selectedImageUrl = useMemo(() => {
    if (selectedId === null) {
      return "";
    }
    return getScreenshotImageUrl(selectedId);
  }, [selectedId]);

  const loadScreenshots = async () => {
    setLoading(true);
    setErrorMessage("");
    try {
      const data = await listScreenshots({ startTime, endTime, limit });
      setItems(data);
      if (data.length === 0) {
        setSelectedId(null);
        setSelectedDetail(null);
      }
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "截图查询失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadScreenshots();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onSearchSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void loadScreenshots();
  };

  const onSelectItem = async (id: number) => {
    setSelectedId(id);
    setDetailLoading(true);
    setErrorMessage("");
    try {
      const detail = await getScreenshot(id);
      setSelectedDetail(detail);
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "截图详情加载失败");
      setSelectedDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <section className="grid gap-6 lg:grid-cols-[1.25fr_1fr]">
      <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-4 text-xl font-semibold">截图列表</h2>
        <form className="grid gap-3 md:grid-cols-3" onSubmit={onSearchSubmit}>
          <label className="text-sm font-medium text-slate-700">
            起始时间
            <input
              type="datetime-local"
              value={startTime}
              onChange={(event) => setStartTime(event.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-2 py-2"
            />
          </label>
          <label className="text-sm font-medium text-slate-700">
            结束时间
            <input
              type="datetime-local"
              value={endTime}
              onChange={(event) => setEndTime(event.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-2 py-2"
            />
          </label>
          <label className="text-sm font-medium text-slate-700">
            条数
            <input
              type="number"
              min={1}
              max={1000}
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value) || 1)}
              className="mt-1 w-full rounded-md border border-slate-300 px-2 py-2"
            />
          </label>
          <button
            type="submit"
            className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 md:col-span-3 md:w-40"
          >
            {loading ? "查询中..." : "查询截图"}
          </button>
        </form>

        {errorMessage && <p className="mt-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{errorMessage}</p>}

        <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-slate-600">
              <tr>
                <th className="px-3 py-2">时间</th>
                <th className="px-3 py-2">状态</th>
                <th className="px-3 py-2">OCR 摘要</th>
                <th className="px-3 py-2">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {items.length === 0 && !loading ? (
                <tr>
                  <td colSpan={4} className="px-3 py-5 text-center text-slate-500">
                    暂无截图数据
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id} className={item.id === selectedId ? "bg-cyan-50" : ""}>
                    <td className="px-3 py-2">{formatTime(item.captured_at)}</td>
                    <td className="px-3 py-2">{item.ocr_status}</td>
                    <td className="px-3 py-2 text-slate-600">{item.ocr_text ? item.ocr_text.slice(0, 42) : "-"}</td>
                    <td className="px-3 py-2">
                      <button
                        type="button"
                        onClick={() => {
                          void onSelectItem(item.id);
                        }}
                        className="rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:border-slate-400"
                      >
                        查看详情
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </article>

      <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-4 text-xl font-semibold">截图详情</h2>
        {detailLoading && <p className="text-sm text-slate-500">详情加载中...</p>}
        {!selectedDetail && !detailLoading && <p className="text-sm text-slate-500">请选择一条截图记录查看原图和元数据</p>}
        {selectedDetail && (
          <div className="space-y-3" data-testid="screenshot-detail">
            <img
              src={selectedImageUrl}
              alt="Screenshot preview"
              className="w-full rounded-lg border border-slate-200 bg-slate-100 object-contain"
            />
            <dl className="grid grid-cols-2 gap-2 rounded-md bg-slate-50 p-3 text-sm">
              <dt className="font-medium text-slate-600">ID</dt>
              <dd>{selectedDetail.id}</dd>
              <dt className="font-medium text-slate-600">窗口</dt>
              <dd>{selectedDetail.window_title || "-"}</dd>
              <dt className="font-medium text-slate-600">进程</dt>
              <dd>{selectedDetail.process_name || "-"}</dd>
              <dt className="font-medium text-slate-600">OCR 状态</dt>
              <dd>{selectedDetail.ocr_status}</dd>
            </dl>
            <p className="rounded-md bg-slate-50 p-3 text-sm text-slate-700">{selectedDetail.ocr_text || "暂无 OCR 文本"}</p>
          </div>
        )}
      </article>
    </section>
  );
}

function ConfigPage() {
  const [config, setConfig] = useState<Record<string, string>>({});
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const loadConfig = async () => {
    setLoading(true);
    setMessage("");
    try {
      const payload = await getConfig();
      setConfig(payload);
      setDraft(payload);
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "配置加载失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadConfig();
  }, []);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      const payload = await updateConfig(draft);
      setConfig(payload);
      setDraft(payload);
      setMessage("配置已更新");
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "配置更新失败");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold">动态配置</h2>
      {loading && <p className="text-sm text-slate-500">配置加载中...</p>}
      {!loading && (
        <form className="space-y-3" onSubmit={onSubmit}>
          {Object.keys(config).length === 0 ? (
            <p className="text-sm text-slate-500">当前无配置项</p>
          ) : (
            Object.keys(config).map((key) => (
              <label key={key} className="block text-sm font-medium text-slate-700">
                {key}
                <input
                  type="text"
                  value={draft[key] ?? ""}
                  onChange={(event) =>
                    setDraft((previous) => ({
                      ...previous,
                      [key]: event.target.value,
                    }))
                  }
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                />
              </label>
            ))
          )}
          <div className="flex gap-2">
            <button type="submit" className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white" disabled={saving}>
              {saving ? "保存中..." : "保存配置"}
            </button>
            <button
              type="button"
              onClick={() => {
                setDraft(config);
                setMessage("");
              }}
              className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700"
            >
              重置
            </button>
          </div>
        </form>
      )}
      {message && <p className="mt-4 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">{message}</p>}
    </section>
  );
}

function SummariesPage() {
  const [startTime, setStartTime] = useState(() => formatDefaultDate(-24));
  const [endTime, setEndTime] = useState(() => formatDefaultDate(0));
  const [items, setItems] = useState<SummaryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const loadSummaries = async () => {
    setLoading(true);
    setMessage("");
    try {
      const data = await listSummaries({ startTime, endTime });
      setItems(data);
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "摘要查询失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadSummaries();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void loadSummaries();
  };

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold">摘要列表</h2>
      <form className="grid gap-3 md:grid-cols-3" onSubmit={onSubmit}>
        <label className="text-sm font-medium text-slate-700">
          起始时间
          <input
            type="datetime-local"
            value={startTime}
            onChange={(event) => setStartTime(event.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-2 py-2"
          />
        </label>
        <label className="text-sm font-medium text-slate-700">
          结束时间
          <input
            type="datetime-local"
            value={endTime}
            onChange={(event) => setEndTime(event.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-2 py-2"
          />
        </label>
        <button type="submit" className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white md:self-end">
          {loading ? "查询中..." : "查询摘要"}
        </button>
      </form>

      {message && <p className="mt-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</p>}

      <ul className="mt-4 space-y-3">
        {items.length === 0 && !loading ? (
          <li className="rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-500">暂无摘要数据</li>
        ) : (
          items.map((item) => (
            <li key={item.id} className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm">
              <p className="font-medium text-slate-800">#{item.id} {formatTime(item.start_time)} - {formatTime(item.end_time)}</p>
              <p className="mt-1 text-slate-700">{item.summary}</p>
              <p className="mt-1 text-xs text-slate-500">activity: {item.activity_type || "unknown"} / created: {formatTime(item.created_at)}</p>
            </li>
          ))
        )}
      </ul>
    </section>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}
