import { useMemo, useState } from "react";
import PageLayout from "../layout/PageLayout";
import EmptyState from "../components/EmptyState";
import JobCard from "../components/JobCard";
import ReturnToDashboardButton from "../components/ReturnToDashboardButton";
import { getBookmarkedJobs } from "../services/session";

/*
  Saved jobs page.
  Displays bookmarked jobs and allows searching across key job fields.
*/
export default function SavedJobsPage() {
    const [query, setQuery] = useState("");
    const savedJobs = getBookmarkedJobs();

    const filteredJobs = useMemo(() => {
        const q = query.trim().toLowerCase();

        if (!q) return savedJobs;

        return savedJobs.filter((job) => {
            const searchableText = [
                job.job_title,
                job.role,
                job.company_name,
                job.location,
                job.country,
                job.work_type,
            ]
                .filter(Boolean)
                .join(" ")
                .toLowerCase();

            return searchableText.includes(q);
        });
    }, [savedJobs, query]);

    return (
        <PageLayout>
            <div>
                <ReturnToDashboardButton />

                <h1 className="section-title">Saved jobs</h1>
                <p className="section-subtitle">
                    Revisit bookmarked opportunities and compare them later.
                </p>
            </div>

            <div className="card mt-8 p-5">
                <input
                    className="input"
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search saved jobs by title, company, role, or location"
                />
            </div>

            <div className="mt-8">
                {!savedJobs.length ? (
                    <EmptyState
                        title="No saved jobs yet"
                        description="Bookmark jobs from your recommendations to view them later."
                    />
                ) : !filteredJobs.length ? (
                    <EmptyState
                        title="No matching saved jobs"
                        description="Try a different search term."
                    />
                ) : (
                    <div className="space-y-5">
                        {filteredJobs.map((job) => (
                            <JobCard key={job.job_id} job={job} profile={null} />
                        ))}
                    </div>
                )}
            </div>
        </PageLayout>
    );
}
