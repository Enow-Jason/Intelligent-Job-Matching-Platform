const steps = [
    {
        title: "Upload your CV",
        description:
            "Add your resume and basic profile details so the system understands your background.",
    },
    {
        title: "Get AI-matched roles",
        description:
            "We rank opportunities by semantic fit, experience alignment, and relevant skills.",
    },
    {
        title: "Understand your fit",
        description:
            "See why each role was recommended and where you may need to upskill.",
    },
];

export default function HowItWorks() {
    return (
        <section className="container-shell py-16 sm:py-20">
            <div className="mx-auto max-w-2xl text-center">
                <h2 className="section-title">How it works</h2>
                <p className="section-subtitle mx-auto">
                    A simple workflow designed to reduce job search friction for graduates.
                </p>
            </div>

            <div className="mt-10 grid gap-6 md:grid-cols-3">
                {steps.map((step, index) => (
                    <div key={step.title} className="card p-6">
                        <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-full bg-indigo-100 text-sm font-bold text-indigo-700">
                            {index + 1}
                        </div>
                        <h3 className="text-lg font-semibold text-slate-900">{step.title}</h3>
                        <p className="mt-2 text-sm leading-6 text-slate-600">
                            {step.description}
                        </p>
                    </div>
                ))}
            </div>
        </section>
    );
}
