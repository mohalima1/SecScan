import { ApiError } from "./api.ts";
import type { Language, Translation } from "./translations.ts";

export function friendlyError(cause: unknown, language: Language, t: Translation): string {
  if (language === "en") {
    if (cause instanceof Error) return cause.message;
    if (typeof cause === "string" && cause) return cause;
    return t.requestFailed;
  }
  if (cause instanceof ApiError) {
    if (cause.status === 403) return t.errors.forbidden;
    if (cause.status === 404) return t.errors.notFound;
    if (cause.status === 409) return t.errors.conflict;
    if (cause.status === 429) return t.errors.rateLimit;
    if (cause.status >= 500) return t.errors.service;
    return t.errors.request;
  }
  return cause instanceof Error ? t.errors.connection : t.errors.request;
}
