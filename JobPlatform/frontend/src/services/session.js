/*
  Frontend session utility layer.

  Stores:
  - authenticated user
  - latest recommendation result
  - saved/bookmarked jobs (scoped per user)
*/

const AUTH_USER_KEY = "authUser";
const RECOMMENDATION_DATA_KEY = "recommendationData";

/* Save authenticated user object */
export function setAuthUser(user) {
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

/* Read authenticated user object */
export function getAuthUser() {
    const raw = localStorage.getItem(AUTH_USER_KEY);
    return raw ? JSON.parse(raw) : null;
}

/* Check if a user is logged in */
export function isAuthenticated() {
    return !!getAuthUser();
}

/* Save recommendation result */
export function setRecommendationData(data) {
    sessionStorage.setItem(RECOMMENDATION_DATA_KEY, JSON.stringify(data));
}

/* Read recommendation result */
export function getRecommendationData() {
    const raw = sessionStorage.getItem(RECOMMENDATION_DATA_KEY);
    return raw ? JSON.parse(raw) : null;
}

/* Clear recommendation data only */
export function clearRecommendationData() {
    sessionStorage.removeItem(RECOMMENDATION_DATA_KEY);
}

/*
  Build a per-user localStorage key.
  This prevents one account from seeing another account's saved jobs.
*/
function getScopedKey(baseKey) {
    const user = getAuthUser();
    const userId = user?.email?.toLowerCase()?.trim();

    if (!userId) {
        return `${baseKey}:anonymous`;
    }

    return `${baseKey}:${userId}`;
}

/* Get bookmarked jobs for the current logged-in user */
export function getBookmarkedJobs() {
    const raw = localStorage.getItem(getScopedKey("bookmarkedJobs"));
    return raw ? JSON.parse(raw) : [];
}

/* Save bookmarked jobs for the current logged-in user */
export function setBookmarkedJobs(jobs) {
    localStorage.setItem(getScopedKey("bookmarkedJobs"), JSON.stringify(jobs));
}

/* Check if a job is bookmarked */
export function isJobBookmarked(jobId) {
    const jobs = getBookmarkedJobs();
    return jobs.some((job) => job.job_id === jobId);
}

/* Add a bookmarked job */
export function addBookmarkedJob(job) {
    const jobs = getBookmarkedJobs();

    if (jobs.some((item) => item.job_id === job.job_id)) {
        return jobs;
    }

    const updated = [job, ...jobs];
    setBookmarkedJobs(updated);
    return updated;
}

/* Remove a bookmarked job */
export function removeBookmarkedJob(jobId) {
    const jobs = getBookmarkedJobs();
    const updated = jobs.filter((job) => job.job_id !== jobId);
    setBookmarkedJobs(updated);
    return updated;
}

/* Toggle bookmark state */
export function toggleBookmarkedJob(job) {
    if (isJobBookmarked(job.job_id)) {
        return removeBookmarkedJob(job.job_id);
    }
    return addBookmarkedJob(job);
}

/* Full logout cleanup */
export function clearUserSession() {
    localStorage.removeItem(AUTH_USER_KEY);
    sessionStorage.removeItem(RECOMMENDATION_DATA_KEY);
}
