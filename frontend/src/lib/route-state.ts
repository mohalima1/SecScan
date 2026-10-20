type PageTitles = { home: string; scanner: string; notFound: string };

export function routeTitle(pathname: string, titles: PageTitles): string {
  if (["/", "/scanner", "/login", "/auth-system.html"].includes(pathname)) return `${titles.scanner} · ${titles.home}`;
  return `${titles.notFound} · ${titles.home}`;
}

export function focusPageHeading(documentRoot: Document): boolean {
  const heading = documentRoot.querySelector<HTMLElement>("main h1");
  if (!heading) return false;
  if (!heading.hasAttribute("tabindex")) heading.setAttribute("tabindex", "-1");
  heading.focus({ preventScroll: true });
  return true;
}
