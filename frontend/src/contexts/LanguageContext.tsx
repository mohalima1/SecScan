import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { type Language, getTranslation } from "@/lib/translations";

type LanguageState = { language: Language; setLanguage: (language: Language) => void; t: ReturnType<typeof getTranslation>; isRTL: boolean };
const LanguageContext = createContext<LanguageState | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>(() => {
    try { return localStorage.getItem("secscan_language") === "ar" ? "ar" : "en"; }
    catch { return "en"; }
  });
  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = language === "ar" ? "rtl" : "ltr";
    try { localStorage.setItem("secscan_language", language); } catch { /* Preference storage is optional. */ }
  }, [language]);
  return <LanguageContext.Provider value={{ language, setLanguage, t: getTranslation(language), isRTL: language === "ar" }}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useLanguage must be inside LanguageProvider");
  return context;
}
