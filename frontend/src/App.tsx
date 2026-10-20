import { useEffect, useRef } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { LanguageProvider } from "@/contexts/LanguageContext";
import Scanner from "./pages/Scanner";
import NotFound from "./pages/NotFound";
import { focusPageHeading, routeTitle } from "@/lib/route-state";
import { useLanguage } from "@/contexts/LanguageContext";

function RouteEffects() {
  const location = useLocation();
  const { t } = useLanguage();
  const previousPath = useRef(location.pathname);
  useEffect(() => {
    document.title = routeTitle(location.pathname, t.pageTitles);
    document.querySelector<HTMLMetaElement>('meta[name="description"]')?.setAttribute("content", t.metaDescription);
    if (previousPath.current !== location.pathname) focusPageHeading(document);
    previousPath.current = location.pathname;
  }, [location.pathname, t]);
  return null;
}

export default function App() {
  return (
    <LanguageProvider><BrowserRouter><RouteEffects /><Routes>
      <Route path="/" element={<Scanner />} />
      <Route path="/login" element={<Navigate to="/" replace />} />
      <Route path="/auth-system.html" element={<Navigate to="/" replace />} />
      <Route path="/scanner" element={<Navigate to="/" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes></BrowserRouter></LanguageProvider>
  );
}
