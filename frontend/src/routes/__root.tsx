import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";

function NotFoundComponent() {
  return (
    <div className="flex min-h-dvh items-center justify-center bg-background px-6">
      <div className="max-w-md">
        <div className="label-eyebrow mb-6">ATLASS · 404</div>
        <h1 className="text-display text-5xl text-foreground">Off the citation graph.</h1>
        <p className="mt-4 text-[15px] leading-relaxed text-muted-foreground">
          The route you followed doesn't resolve to a known surface. No evidence was grounded here.
        </p>
        <div className="mt-8 flex gap-3">
          <Link
            to="/"
            className="inline-flex h-9 items-center rounded-md bg-primary px-4 text-[13px] font-medium text-primary-foreground transition hover:opacity-90"
          >
            Return to landing
          </Link>
          <Link
            to="/app"
            className="inline-flex h-9 items-center rounded-md border border-hairline-strong bg-surface px-4 text-[13px] font-medium text-foreground transition hover:bg-surface-2"
          >
            Open workspace
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);

  return (
    <div className="flex min-h-dvh items-center justify-center bg-background px-6">
      <div className="max-w-md">
        <div className="label-eyebrow mb-6 text-[color:var(--danger)]">Runtime · Recoverable</div>
        <h1 className="text-display text-4xl text-foreground">A stage failed to render.</h1>
        <p className="mt-4 text-[15px] leading-relaxed text-muted-foreground">
          The interface caught an error before it reached you. Nothing was persisted incorrectly.
        </p>
        <pre className="mt-6 max-h-40 overflow-auto rounded-md border border-hairline bg-surface p-3 font-mono text-[12px] text-muted-foreground">
          {error.message}
        </pre>
        <div className="mt-6 flex gap-3">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="inline-flex h-9 items-center rounded-md bg-primary px-4 text-[13px] font-medium text-primary-foreground transition hover:opacity-90"
          >
            Retry render
          </button>
          <a
            href="/"
            className="inline-flex h-9 items-center rounded-md border border-hairline-strong bg-surface px-4 text-[13px] font-medium text-foreground transition hover:bg-surface-2"
          >
            Return to landing
          </a>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "ATLASS — Paper to working system" },
      {
        name: "description",
        content:
          "ATLASS turns scientific papers into evidence-grounded specifications, implementation blueprints, and runnable PyTorch baselines.",
      },
      { name: "author", content: "ATLASS" },
      { name: "theme-color", content: "#0d1017" },
      { property: "og:title", content: "ATLASS — Paper to working system" },
      {
        property: "og:description",
        content:
          "An AI research cognition system: paper → evidence → specification → blueprint → baseline → report.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,500&family=JetBrains+Mono:wght@400;500&display=swap",
      },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  return (
    <QueryClientProvider client={queryClient}>
      <Outlet />
    </QueryClientProvider>
  );
}
