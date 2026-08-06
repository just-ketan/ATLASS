import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useAtlassUser } from "@/lib/atlass-store";
import { ArrowRight } from "lucide-react";

export const Route = createFileRoute("/login")({
  component: Login,
  head: () => ({
    meta: [{ title: "Login — ATLASS" }],
  }),
});

function Login() {
  const { signIn, authError } = useAtlassUser();
  const navigate = useNavigate();
  
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !name) return;
    
    setLoading(true);
    const user = await signIn(email, name);
    setLoading(false);
    
    if (user) {
      navigate({ to: "/app" });
    }
  };

  return (
    <div className="relative flex min-h-dvh flex-col justify-center overflow-hidden bg-background px-6 text-foreground sm:px-10">
      {/* Ambient background */}
      <div className="pointer-events-none absolute inset-0 grid-bg opacity-40" aria-hidden />
      <div
        className="pointer-events-none absolute -left-40 top-[20%] size-[720px] rounded-full opacity-[0.14] blur-3xl"
        style={{ background: "radial-gradient(circle, var(--evidence) 0%, transparent 60%)" }}
        aria-hidden
      />

      <div className="relative z-10 mx-auto w-full max-w-[400px]">
        <div className="flex flex-col items-center text-center">
          <span className="relative inline-flex size-10 items-center justify-center rounded-lg border border-hairline-strong bg-surface shadow-[var(--shadow-panel)]">
            <span className="absolute inset-[3px] rounded-[5px] bg-linear-to-br from-[color:var(--evidence)]/60 to-transparent" />
            <span className="relative text-mono text-[14px] font-semibold text-foreground">Λ</span>
          </span>
          <h1 className="mt-6 text-display text-3xl tracking-tight">Sign in to ATLASS</h1>
          <p className="mt-2 text-[14px] text-muted-foreground">
            Access your research workspace and papers.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4 rounded-xl border border-hairline-strong bg-surface/50 p-6 shadow-[var(--shadow-float)] backdrop-blur-md">
          {authError && (
            <div className="rounded-md border border-[color:var(--danger)]/30 bg-[color:var(--danger-soft)]/40 p-3 text-[13px] text-[color:var(--danger)]">
              {authError}
            </div>
          )}
          
          <div className="space-y-1.5">
            <label className="text-[12px] font-medium text-foreground">Full Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ada Lovelace"
              required
              className="h-10 w-full rounded-md border border-hairline-strong bg-background px-3 text-[13px] text-foreground placeholder:text-muted-foreground focus:border-[color:var(--evidence)] focus:outline-none focus:ring-1 focus:ring-[color:var(--evidence)]"
            />
          </div>
          
          <div className="space-y-1.5">
            <label className="text-[12px] font-medium text-foreground">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="ada@example.com"
              required
              className="h-10 w-full rounded-md border border-hairline-strong bg-background px-3 text-[13px] text-foreground placeholder:text-muted-foreground focus:border-[color:var(--evidence)] focus:outline-none focus:ring-1 focus:ring-[color:var(--evidence)]"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !email || !name}
            className="group mt-6 inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-primary px-4 text-[13px] font-medium text-primary-foreground transition hover:opacity-90 disabled:opacity-60"
          >
            {loading ? "Authenticating…" : "Continue"}
            {!loading && <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" />}
          </button>
        </form>

        <p className="mt-6 text-center text-[12px] text-subtle">
          ATLASS uses OAuth strictly for session persistence. <br />
          No external provider integration is required for this demo.
        </p>
      </div>
    </div>
  );
}
