import { Check, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useLanguage } from "@/contexts/LanguageContext";

type Props = { name: string; description: string; icon: LucideIcon; selected: boolean; available: boolean; disabled: boolean; onToggle: () => void };
export default function ToolCard({ name, description, icon: Icon, selected, available, disabled, onToggle }: Props) {
  const { t } = useLanguage();
  return <button type="button" aria-pressed={selected} disabled={disabled || !available} onClick={onToggle}
    className={cn("flex w-full cursor-pointer items-start gap-4 rounded-lg border p-5 text-start transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:border-border disabled:bg-card", disabled && "opacity-80", selected ? "border-primary bg-selection" : "border-border bg-card hover:border-primary")}>
    <Icon className={cn("mt-1 h-5 w-5 shrink-0", available ? "text-primary" : "text-muted-foreground")} aria-hidden="true" />
    <span className="min-w-0 flex-1"><span className="flex flex-wrap items-center justify-between gap-2 font-semibold">{name}{selected && <Check className="h-4 w-4" aria-hidden="true" />}</span>
      <span className="mt-2 block text-sm text-muted-foreground">{description}</span>
      <span className={cn("mt-3 block text-sm font-medium", available ? "text-success" : "text-muted-foreground")}>{available ? t.available : t.unavailable}</span></span>
  </button>;
}
