import { Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Github, Menu, X } from "lucide-react";
import { cn } from "@/lib/utils";
import logo from "@/assets/praxis-logo-static.png";

const NAV = [
  { label: "Home", to: "/" },
  { label: "Try Praxis", to: "/try" },
  { label: "How It Works", to: "/how-it-works" },
  { label: "Documentation", to: "/docs" },
  { label: "Validation", to: "/validation" },
  { label: "Security", to: "/security" },
  { label: "FAQ", to: "/faq" },
] as const;

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "sticky top-0 z-50 w-full border-b transition-all duration-300",
        scrolled
          ? "border-border bg-background/85 backdrop-blur-xl"
          : "border-transparent bg-background/40 backdrop-blur-sm",
      )}
    >
      <div
        className={cn(
          "mx-auto flex w-full max-w-7xl items-center gap-4 px-5 transition-all duration-300 sm:px-8",
          scrolled ? "h-13 py-2" : "h-16 py-3",
        )}
      >
        <Link to="/" className="group flex items-center gap-2.5 font-mono text-sm font-semibold tracking-[0.18em]">
          <span className="grid h-9 w-9 shrink-0 place-items-center">
            <img
              src={logo}
              alt="Praxis logo"
              width={36}
              height={36}
              className="h-9 w-9 object-contain"
            />
          </span>
          <span>
            PRAXIS<span className="text-primary soft-pulse">_</span>
          </span>
        </Link>

        <nav className="ml-4 hidden items-center gap-0.5 lg:flex">
          {NAV.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              activeOptions={{ exact: item.to === "/" }}
              className="rounded-md px-2.5 py-1.5 text-[13px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              activeProps={{ className: "text-foreground bg-accent/60" }}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <a
            href="https://github.com/Debopom26/Praxis_"
            target="_blank"
            rel="noreferrer"
            aria-label="GitHub"
            className="hidden h-8 w-8 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:border-border-strong hover:text-foreground sm:inline-flex"
          >
            <Github className="h-4 w-4" />
          </a>
          <button
            onClick={() => setOpen((v) => !v)}
            aria-label="Menu"
            className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border text-muted-foreground lg:hidden"
          >
            {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {open ? (
        <div className="border-t border-border bg-background/95 backdrop-blur-xl lg:hidden">
          <nav className="mx-auto grid max-w-7xl gap-1 px-5 py-3 sm:px-8">
            {NAV.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                onClick={() => setOpen(false)}
                className="rounded-md px-2 py-2.5 text-sm text-muted-foreground hover:bg-accent hover:text-foreground"
                activeProps={{ className: "text-foreground" }}
                activeOptions={{ exact: item.to === "/" }}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      ) : null}
    </header>
  );
}
