import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { Shield, Network, Globe, Database, Server, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { LanguageToggle } from "@/components/LanguageToggle";
import ToolCard from "@/components/scanner/ToolCard";
import ScanProgress from "@/components/scanner/ScanProgress";
import ScanResults from "@/components/scanner/ScanResults";
import { useLanguage } from "@/contexts/LanguageContext";
import { downloadReport, getHistory, getScanResults, getScanStatus, getToolStatus, startScan, type ScanResult, type ScanStatus, type ToolId, type ToolStatus } from "@/lib/api";
import { isActiveScan } from "@/lib/scan-state";
import { settleScannerOverview } from "@/lib/scanner-overview";
import { friendlyError } from "@/lib/errors";

const tools: Array<{ id: ToolId; icon: typeof Network }> = [
  { id: "nmap", icon: Network }, { id: "zap", icon: Globe },
  { id: "sqlmap", icon: Database }, { id: "nikto", icon: Server },
];
const scanStatusStyles: Record<ScanStatus["status"], string> = {
  queued: "text-warning", running: "text-primary", finished: "text-success", error: "text-destructive",
};
export default function Scanner() {
  const { t, language } = useLanguage();
  const [target, setTarget] = useState("");
  const [selected, setSelected] = useState<ToolId[]>([]);
  const [toolStatus, setToolStatus] = useState<ToolStatus | null>(null);
  const [history, setHistory] = useState<ScanStatus[]>([]);
  const [scanId, setScanId] = useState<string | null>(null);
  const [scan, setScan] = useState<ScanStatus | null>(null);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");
  const [pollError, setPollError] = useState("");
  const [historyError, setHistoryError] = useState("");
  const [toolsError, setToolsError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setHistoryError(""); setToolsError("");
    void settleScannerOverview(getHistory(controller.signal), getToolStatus(controller.signal)).then(overview => {
      if (controller.signal.aborted) return;
      setHistoryError(overview.historyError); setToolsError(overview.toolsError);
      if (overview.history) {
        setHistory(overview.history.scans);
        const active = overview.history.scans.find(isActiveScan);
        if (active) { setScanId(active.scan_id); setTarget(active.target); }
      }
      if (overview.tools) setToolStatus(overview.tools);
    });
    return () => controller.abort();
  }, [retry]);

  useEffect(() => {
    if (!scanId) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    setPollError("");
    async function poll() {
      try {
        const status = await getScanStatus(scanId!, controller.signal);
        if (controller.signal.aborted) return;
        setScan(status);
        if (isActiveScan(status)) {
          timer = setTimeout(() => void poll(), 2000);
        } else {
          try {
            const finished = await getScanResults(scanId!, controller.signal);
            if (!controller.signal.aborted) setResult(finished);
          } catch (cause) {
            if (!controller.signal.aborted) setError(friendlyError(status.error || cause, language, t));
          }
          const recent = await getHistory(controller.signal);
          if (!controller.signal.aborted) setHistory(recent.scans);
        }
      } catch (cause) { if (!controller.signal.aborted) setPollError(friendlyError(cause, language, t)); }
    }
    void poll();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [scanId, retry, language, t]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (!target.trim()) { setError(t.errorTarget); return; }
    const available = selected.filter(tool => toolStatus?.tools[tool].available);
    if (!available.length) { setError(t.errorTools); return; }
    setSubmitting(true);
    try {
      const started = await startScan(target.trim(), available);
      setScan(null); setResult(null); setPollError(""); setScanId(started.scan_id);
    } catch (cause) { setError(friendlyError(cause, language, t)); }
    finally { setSubmitting(false); }
  }

  async function exportReport(format: "pdf" | "html") {
    if (!result) return;
    setDownloading(true);
    try { await downloadReport(result.scan_id, format); }
    catch (cause) { setError(friendlyError(cause, language, t)); }
    finally { setDownloading(false); }
  }
  function openScan(item: ScanStatus) {
    setError(""); setPollError(""); setResult(null); setScan(item);
    setTarget(item.target);
    if (scanId === item.scan_id) setRetry(value => value + 1);
    else setScanId(item.scan_id);
  }

  const active = submitting || isActiveScan(scan) || Boolean(scanId && !scan && !pollError);
  return (
    <div className="min-h-screen">
      <a href="#scanner-main" className="sr-only focus:not-sr-only focus:fixed focus:start-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-3 focus:font-medium focus:text-primary-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">{t.skipToScanner}</a>
      <header className="border-b">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-5">
          <Link to="/" className="flex min-w-0 items-center gap-2 text-lg font-semibold focus-visible:rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-4 focus-visible:ring-offset-background sm:text-xl"><Shield className="shrink-0 text-primary" aria-hidden="true" /><span className="break-words">{t.title}</span></Link>
          <LanguageToggle />
        </div>
      </header>
      <main id="scanner-main" className="mx-auto max-w-6xl space-y-10 px-5 py-8">
        <div><h1 className="text-3xl font-semibold">{t.scannerTitle}</h1><p className="mt-3 max-w-prose text-muted-foreground">{t.authorizedUse}</p></div>
        <form onSubmit={submit} className="space-y-6">
          <div className="space-y-3"><label htmlFor="target" className="block font-semibold">{t.target}</label>
            <div className="flex flex-col gap-3 sm:flex-row"><Input id="target" dir="ltr" className="flex-1" value={target} onChange={event => setTarget(event.target.value)} placeholder={t.targetPlaceholder} aria-describedby="target-help scan-scope" required maxLength={2048} disabled={active} /><Button disabled={active || !toolStatus}>{active ? t.scanning : t.startScan}</Button></div>
            <p id="target-help" className="text-sm text-muted-foreground">{t.targetHint}</p>
            <p id="scan-scope" className="break-words text-sm">{t.scope}: <bdi>{toolStatus?.allowed_hosts.join(", ") || "…"}</bdi></p>
          </div>
          <fieldset disabled={active}><legend className="mb-4 text-lg font-semibold">{t.selectTools}</legend>
            {!toolStatus && !toolsError && <p className="mb-3 text-sm text-muted-foreground" role="status">{t.toolsLoading}</p>}
            {toolsError && <p role="alert" className="mb-4 break-words text-destructive">{friendlyError(toolsError, language, t)}</p>}
            <div className="grid gap-4 sm:grid-cols-2">
              {tools.map(({ id, icon }) => <ToolCard key={id} icon={icon} name={t.tools[id].name} description={t.tools[id].description} selected={selected.includes(id)} available={toolStatus?.tools[id].available ?? false} disabled={active} onToggle={() => setSelected(current => current.includes(id) ? current.filter(tool => tool !== id) : [...current, id])} />)}
            </div>
            <p className="mt-3 text-sm text-muted-foreground">{t.toolDescription}</p>
            <Button type="button" variant="outline" className="mt-3" disabled={active} onClick={() => setRetry(value => value + 1)}>{t.retryTools}</Button>
          </fieldset>
        </form>
        {error && <div className="space-y-3"><p role="alert" className="break-words text-destructive">{error}</p><Button variant="outline" onClick={() => { setError(""); setRetry(value => value + 1); }}>{t.retry}</Button></div>}
        {pollError && <div className="space-y-3"><p role="alert" className="break-words text-destructive">{pollError}</p><Button variant="outline" onClick={() => setRetry(value => value + 1)}>{t.retryScan}</Button></div>}
        {scan && <ScanProgress scan={scan} />}
        {result && <section className="space-y-6 border-t pt-8" aria-labelledby="results-heading">
          <div className="flex flex-wrap items-center justify-between gap-4"><h2 id="results-heading" className="text-2xl font-semibold">{t.scanResults}</h2>
            <div className="flex flex-wrap gap-3"><Button variant="outline" disabled={downloading} onClick={() => void exportReport("pdf")}><Download aria-hidden="true" />{downloading ? t.downloadingReport : t.exportReport}</Button><Button variant="outline" disabled={downloading} onClick={() => void exportReport("html")}>{downloading ? t.downloadingReport : t.exportHtml}</Button></div>
          </div>
          <ScanResults result={result} />
        </section>}
        <section className="border-t pt-8" aria-labelledby="history-heading"><h2 id="history-heading" className="mb-4 text-xl font-semibold">{t.history}</h2>
          {historyError ? <div className="space-y-3"><p role="alert" className="break-words text-destructive">{friendlyError(historyError, language, t)}</p><Button variant="outline" onClick={() => setRetry(value => value + 1)}>{t.retryHistory}</Button></div> : history.length ? <ul className="divide-y divide-border">{history.map(item => <li key={item.scan_id}><button type="button" onClick={() => openScan(item)} className="flex w-full flex-wrap items-center justify-between gap-3 py-4 text-start hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"><span className="min-w-0 break-all"><bdi>{item.target}</bdi><span className="mt-1 block text-sm text-muted-foreground">{new Date(item.created_at * 1000).toLocaleString(language)}</span></span><span className={scanStatusStyles[item.status]}>{t[item.status]}</span></button></li>)}</ul> : <p className="text-muted-foreground">{t.noHistory}</p>}
        </section>
      </main>
    </div>
  );
}
