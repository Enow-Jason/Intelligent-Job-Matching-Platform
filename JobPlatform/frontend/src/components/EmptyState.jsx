export default function EmptyState({
                                       title = "No results yet",
                                       description = "Upload your CV to generate personalised job recommendations.",
                                   }) {
    return (
        <div className="card flex min-h-[280px] flex-col items-center justify-center p-8 text-center">
            <div className="mb-4 rounded-full bg-slate-100 p-4">
                <span className="text-2xl">✨</span>
            </div>
            <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
            <p className="mt-2 max-w-md text-sm text-slate-600">{description}</p>
        </div>
    );
}
