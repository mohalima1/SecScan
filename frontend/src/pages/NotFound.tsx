import { Link } from "react-router-dom";
import { useLanguage } from "@/contexts/LanguageContext";

export default function NotFound() {
  const { t } = useLanguage();
  return <main className="mx-auto max-w-xl px-5 py-24"><h1 className="text-3xl font-semibold">{t.pageTitles.notFound}</h1><p className="mt-4 text-muted-foreground">{t.pageNotFound}</p><Link to="/" className="mt-6 inline-block text-primary underline underline-offset-4 focus-visible:rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-4 focus-visible:ring-offset-background">{t.returnHome}</Link></main>;
}
