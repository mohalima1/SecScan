import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))", input: "hsl(var(--input))", ring: "hsl(var(--ring))",
        background: "hsl(var(--background))", foreground: "hsl(var(--foreground))",
        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
        secondary: { DEFAULT: "hsl(var(--secondary))", foreground: "hsl(var(--secondary-foreground))" },
        destructive: { DEFAULT: "hsl(var(--destructive))", foreground: "hsl(var(--destructive-foreground))" },
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        accent: { DEFAULT: "hsl(var(--accent))", foreground: "hsl(var(--accent-foreground))" },
        selection: "hsl(var(--selection-surface))",
        success: { DEFAULT: "hsl(var(--success))", surface: "hsl(var(--success-surface))" },
        warning: { DEFAULT: "hsl(var(--warning))", surface: "hsl(var(--warning-surface))" },
        critical: { DEFAULT: "hsl(var(--critical))", border: "hsl(var(--critical-border))", surface: "hsl(var(--critical-surface))" },
        high: { DEFAULT: "hsl(var(--high))", border: "hsl(var(--high-border))", surface: "hsl(var(--high-surface))" },
        medium: { DEFAULT: "hsl(var(--medium))", border: "hsl(var(--medium-border))", surface: "hsl(var(--medium-surface))" },
        low: { DEFAULT: "hsl(var(--low))", border: "hsl(var(--low-border))", surface: "hsl(var(--low-surface))" },
        informational: { DEFAULT: "hsl(var(--informational))", border: "hsl(var(--informational-border))", surface: "hsl(var(--informational-surface))" },
      },
      borderRadius: { lg: "var(--radius)", md: "calc(var(--radius) - 2px)", sm: "calc(var(--radius) - 4px)" },
    },
  },
  plugins: [],
} satisfies Config;
