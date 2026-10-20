import { Languages } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useLanguage } from "@/contexts/LanguageContext";

export function LanguageToggle() {
  const { language, setLanguage } = useLanguage();
  return <Button variant="outline" onClick={() => setLanguage(language === "en" ? "ar" : "en")}><Languages aria-hidden="true" />{language === "en" ? "العربية" : "English"}</Button>;
}
