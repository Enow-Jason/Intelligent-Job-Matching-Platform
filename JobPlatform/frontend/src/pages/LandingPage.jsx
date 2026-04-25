import { Link } from "react-router-dom";
import HowItWorks from "../components/HowItWorks";

export default function LandingPage() {
    return (
        <div className="min-h-screen bg-gradient-to-b from-white to-slate-100">
            <header className="border-b border-slate-200 bg-white/90 backdrop-blur">
                <div className="container-shell flex h-16 items-center justify-between">
                    <div className="text-lg font-bold tracking-tight text-slate-900">
                        GradMatch AI
                    </div>

                    <div className="flex items-center gap-3">
                        <Link to="/signin" className="btn-secondary">
                            Sign In
                        </Link>
                        <Link to="/signup" className="btn-primary">
                            Get Started
                        </Link>
                    </div>
                </div>
            </header>

            <section className="container-shell py-20 sm:py-28">
                <div className="mx-auto max-w-4xl text-center">
          <span className="inline-flex rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-indigo-700">
            AI job matching for graduates
          </span>

                    <h1 className="mt-6 text-4xl font-bold tracking-tight text-slate-900 sm:text-6xl">
                        Upload your CV and discover roles that actually fit.
                    </h1>

                    <p className="mx-auto mt-6 max-w-2xl text-base leading-7 text-slate-600 sm:text-lg">
                        GradMatch AI helps graduates find relevant opportunities faster with
                        CV-based recommendations, skill-gap insights, and clear match explanations.
                    </p>

                    <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
                        <Link to="/signup" className="btn-primary">
                            Get Started
                        </Link>
                        <Link to="/signin" className="btn-secondary">
                            Sign In
                        </Link>
                    </div>
                </div>
            </section>

            <HowItWorks />
        </div>
    );
}
