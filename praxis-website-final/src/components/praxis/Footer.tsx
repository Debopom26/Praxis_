import logo from "@/assets/praxis-logo-static.png";
import { Link } from "@tanstack/react-router";
import { ArrowUpRight } from "lucide-react";

const PRAXIS_APP_URL = "https://praxisdashboard.debopomrc2602.workers.dev/";

export function Footer() {
  return (
    <footer className="hairline-t px-5 py-12 sm:px-8">
      <div className="mx-auto grid w-full max-w-6xl gap-8 md:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <div className="flex items-center gap-2.5 font-mono text-sm font-semibold tracking-[0.18em]">
            <img src={logo} alt="" className="h-9 w-9 object-contain" />
            PRAXIS<span className="text-primary">_</span>
          </div>
          <p className="mt-2 max-w-xs text-sm text-muted-foreground">
            Real-Time Voice Integrity for Live Calls.
          </p>
        </div>
        <div className="grid gap-2 text-sm">
          <div className="label-xs">Product</div>
          <a
            href={PRAXIS_APP_URL}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-muted-foreground hover:text-foreground"
          >
            Try Praxis <ArrowUpRight className="h-3.5 w-3.5" />
          </a>
          <Link to="/how-it-works" className="text-muted-foreground hover:text-foreground">
            How It Works
          </Link>
        </div>
        <div className="grid gap-2 text-sm">
          <div className="label-xs">Resources</div>
          <Link to="/docs" className="text-muted-foreground hover:text-foreground">
            Documentation
          </Link>
          <Link to="/validation" className="text-muted-foreground hover:text-foreground">
            Validation
          </Link>
          <Link to="/security" className="text-muted-foreground hover:text-foreground">
            Security
          </Link>
          <Link to="/faq" className="text-muted-foreground hover:text-foreground">
            FAQ
          </Link>
          <a
            href="https://github.com/Debopom26/Praxis_"
            target="_blank"
            rel="noreferrer"
            className="text-muted-foreground hover:text-foreground"
          >
            GitHub
          </a>
        </div>
      </div>
      <div className="mx-auto mt-10 flex w-full max-w-6xl flex-wrap items-center justify-between gap-3 border-t border-border pt-5 font-mono text-[11px] tracking-[0.1em] text-muted-foreground uppercase">
        <span className="inline-flex items-center gap-2">&copy; 2026 <img src={logo} alt="" className="h-6 w-6 object-contain" /> Praxis_</span>
        <span>Public website · not the authenticated product</span>
      </div>
    </footer>
  );
}
