import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import PageLayout from "../layout/PageLayout";
import EmptyState from "../components/EmptyState";
import JobCard from "../components/JobCard";
import { getRecommendationData } from "../services/session";

/*
  Dashboard page showing recommendation results from the latest upload.
  Includes filter and sorting controls.
*/
export default function DashboardPage() {
    const [data, setData] = useState(null);
    const [filters, setFilters] = useState({
        location: "",
        workType: "",
    });

    const [sortBy, setSortBy] = useState("matchScoreDesc");

    useEffect(() => {
        setData(getRecommendationData());
    }, []);

    const jobs = data?.results || [];
    const parsedProfile = data?.parsed_profile || null;

    const filteredJobs = useMemo(() => {
        let nextJobs = jobs.filter((job) => {
            const matchesLocation =
                !filters.location ||
                `${job.location || ""} ${job.country || ""}`
                    .toLowerCase()
                    .includes(filters.location.toLowerCase());

            const matchesWorkType =
                !filters.workType || (job.work_type || "") === filters.workType;

            return matchesLocation && matchesWorkType;
        });

        // Sorting options for user control
        nextJobs = [...nextJobs].sort((a, b) => {
            if (sortBy === "matchScoreDesc") {
                return (b.final_score || b.semantic_score || 0) - (a.final_score || a.semantic_score || 0);
            }

            if (sortBy === "skillsMatchedDesc") {
                return (b.matched_skills?.length || 0) - (a.matched_skills?.length || 0);
            }

            if (sortBy === "skillsMissingAsc") {
                return (a.missing_skills_top10?.length || 0) - (b.missing_skills_top10?.length || 0);
            }

            if (sortBy === "experienceAsc") {
                return String(a.experience || "").localeCompare(String(b.experience || ""));
            }

            if (sortBy === "titleAsc") {
                return String(a.job_title || "").localeCompare(String(b.job_title || ""));
            }

            return 0;
        });

        return nextJobs;
    }, [jobs, filters, sortBy]);

    return (
        <PageLayout>
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                    <h1 className="section-title">Your recommendations</h1>
                    <p className="section-subtitle">
                        Ranked opportunities tailored to your profile, with clearer role, company, and fit context.
                    </p>
                </div>
            </div>

            {parsedProfile && (
                <div className="card mt-8 p-6">
                    <h2 className="text-lg font-semibold text-slate-900">Profile snapshot</h2>

                    <div className="mt-4 grid gap-4 sm:grid-cols-3">
                        <div>
                            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                                Inferred role
                            </p>
                            <p className="mt-1 text-sm text-slate-800">
                                {parsedProfile.inferred_role || "Not detected"}
                            </p>
                        </div>

                        <div>
                            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                                Experience
                            </p>
                            <p className="mt-1 text-sm text-slate-800">
                                {parsedProfile.experience_years} years
                            </p>
                        </div>

                        <div>
                            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                                Education
                            </p>
                            <p className="mt-1 text-sm text-slate-800">
                                {parsedProfile.education || "Not detected"}
                            </p>
                        </div>
                    </div>
                </div>
            )}

            <div className="card mt-8 p-5">
                <div className="grid gap-4 md:grid-cols-3">
                    <input
                        className="input"
                        placeholder="Filter by location or country"
                        value={filters.location}
                        onChange={(e) =>
                            setFilters((prev) => ({ ...prev, location: e.target.value }))
                        }
                    />

                    <select
                        className="input"
                        value={filters.workType}
                        onChange={(e) =>
                            setFilters((prev) => ({ ...prev, workType: e.target.value }))
                        }
                    >
                        <option value="">All work types</option>
                        <option value="Full-Time">Full-Time</option>
                        <option value="Part-Time">Part-Time</option>
                        <option value="Contract">Contract</option>
                        <option value="Intern">Intern</option>
                        <option value="Temporary">Temporary</option>
                    </select>

                    <select
                        className="input"
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                    >
                        <option value="matchScoreDesc">Sort by match score</option>
                        <option value="skillsMatchedDesc">Sort by skills matched</option>
                        <option value="skillsMissingAsc">Sort by fewer skill gaps</option>
                        <option value="experienceAsc">Sort by experience label</option>
                        <option value="titleAsc">Sort by job title</option>
                    </select>
                </div>
            </div>

            <div className="mt-8">
                {!jobs.length ? (
                    <div className="space-y-6">
                        <EmptyState
                            title="No recommendations yet"
                            description="Complete your recommendation profile and upload your CV to generate tailored job matches."
                        />
                        <div className="flex justify-center">
                            <Link to="/profile" className="btn-primary">
                                Go to Recommendation Profile
                            </Link>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-5">
                        {filteredJobs.map((job) => (
                            <JobCard
                                key={job.job_id}
                                job={job}
                                profile={parsedProfile}
                            />
                        ))}
                    </div>
                )}
            </div>
        </PageLayout>
    );
}
