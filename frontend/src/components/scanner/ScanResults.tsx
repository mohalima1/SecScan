import { type ScanResult, type Severity } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";

const severityOrder: Severity[] = ["critical", "high", "medium", "low", "info"];
const severityStyles: Record<Severity, string> = {
  critical: "border-critical-border bg-critical-surface text-critical",
  high: "border-high-border bg-high-surface text-high",
  medium: "border-medium-border bg-medium-surface text-medium",
  low: "border-low-border bg-low-surface text-low",
  info: "border-informational-border bg-informational-surface text-informational",
};
const executionStyles = {
  completed: "text-success", partial: "text-warning", error: "text-destructive", timeout: "text-warning",
} as const;
const outcomeStyles = { completed: "text-success", partial: "text-warning", error: "text-destructive" } as const;

export default function ScanResults({ result }: { result: ScanResult }) {
  const { t, language } = useLanguage();
  return <div className="space-y-8">
    <div className="space-y-2 break-words tabular-nums">
      <p><strong>{t.target}:</strong> <bdi>{result.target}</bdi></p>
      <p className="text-sm text-muted-foreground">{new Date(result.timestamp).toLocaleString(language)} · {t.duration}: {result.duration_seconds}s</p>
      <p>{t.uniqueIssues}: {result.total_findings} · {t.sourceReports}: {result.raw_finding_count}</p>
      <p className="max-w-prose text-sm text-muted-foreground">{t.verification}</p>
    </div>
    <section aria-labelledby="coverage-heading">
      <h3 id="coverage-heading" className="mb-3 text-lg font-semibold">{t.coverage} · <span className={outcomeStyles[result.outcome]}>{t[result.outcome]}</span></h3>
      <ul className="divide-y divide-border">
        {Object.entries(result.tool_results).map(([tool, state]) => state && <li key={tool} className="py-3">
          <p className="flex flex-wrap justify-between gap-2"><strong>{tool}</strong><span className={executionStyles[state.status]}>{t[state.status]}</span></p>
          {state.error && <p className="mt-2 break-words text-sm text-destructive">{state.error}</p>}
        </li>)}
      </ul>
    </section>
    <section aria-labelledby="issues-heading">
      <h3 id="issues-heading" className="mb-4 text-lg font-semibold">{t.results}</h3>
      <div className="mb-5 flex flex-wrap gap-3">{severityOrder.filter(severity => result.counts[severity] > 0).map(severity => <span key={severity} className={`rounded-full border px-3 py-1 text-sm ${severityStyles[severity]}`}>{t[severity]}: {result.counts[severity]}</span>)}</div>
      {result.findings.length === 0 ? <p className="text-muted-foreground">{t.noFindings}</p> : <div className="divide-y divide-border">
        {result.findings.map(finding => <article key={finding.id} className="space-y-4 py-6 first:pt-0">
          <div className="flex flex-wrap items-center gap-3"><span className={`rounded-full border px-3 py-1 text-sm ${severityStyles[finding.severity]}`}>{t[finding.severity]}</span><h4 className="min-w-0 break-words text-lg font-semibold">{finding.title}</h4></div>
          <p className="text-sm">{t.confidence}: {finding.confidence === "corroborated" ? t.corroborated : t.singleTool} · {finding.tools.join(", ")}</p>
          <p className="break-all text-sm text-muted-foreground"><bdi>{finding.url}</bdi>{finding.parameter && ` · ${t.parameter}: ${finding.parameter}`}</p>
          <p className="max-w-prose break-words">{finding.description}</p>
          {finding.sources.map((source, index) => <details key={`${source.tool}-${index}`} className="rounded-lg border p-4 transition-colors open:border-primary">
            <summary className="cursor-pointer font-medium">{t.evidence} · {source.tool}{source.source_confidence ? ` · ${source.source_confidence}` : ""}</summary>
            <pre dir="ltr" className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap break-words text-sm">{source.evidence || "—"}</pre>
          </details>)}
          {finding.recommendation && <p className="max-w-prose break-words"><strong>{t.remediation}:</strong> {finding.recommendation}</p>}
        </article>)}
      </div>}
    </section>
    <section aria-labelledby="observations-heading">
      <h3 id="observations-heading" className="mb-3 text-lg font-semibold">{t.observations}</h3>
      {result.observations.length ? <ul className="divide-y divide-border">{result.observations.map((item, index) => <li key={index} className="py-3"><p className="break-words font-medium">{item.tool} · {item.title}</p><p className="mt-1 break-words text-sm text-muted-foreground">{[item.service, item.product, item.version, item.description].filter(Boolean).join(" · ")}</p></li>)}</ul> : <p className="text-muted-foreground">{t.noObservations}</p>}
    </section>
  </div>;
}
