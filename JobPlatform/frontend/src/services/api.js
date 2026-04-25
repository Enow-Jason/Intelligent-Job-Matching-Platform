import axios from "axios";

/*
  Central API client for backend communication.
  Spring Boot is the main backend entrypoint.
*/
const api = axios.create({
    baseURL: "http://localhost:8080",
});

/*
  Create a new user account in Spring Boot / MySQL.
*/
export async function signUpUser(data) {
    const payload = {
        firstName: data.firstName,
        lastName: data.lastName,
        pronouns: data.pronouns,
        email: data.email,
        password: data.password,
    };

    const response = await api.post("/api/users/signup", payload);
    return response.data;
}

/*
  Real password-based sign-in.
*/
export async function signInUser(data) {
    const payload = {
        email: data.email,
        password: data.password,
    };

    const response = await api.post("/api/users/signin", payload);
    return response.data;
}

/*
  Change password for a local account.
*/
export async function changeUserPassword(data) {
    const payload = {
        email: data.email,
        currentPassword: data.currentPassword,
        newPassword: data.newPassword,
    };

    const response = await api.post("/api/users/change-password", payload);
    return response.data;
}

/*
  Load profile data for a user by email.
*/
export async function getUserProfile(email) {
    const response = await api.get(`/api/users/profile?email=${encodeURIComponent(email)}`);
    return response.data;
}

/*
  Save recommendation-related profile data.
*/
export async function saveUserProfile(data) {
    const payload = {
        email: data.email,
        location: data.location || "",
        targetRole: data.targetRole || "",
        yearsOfExperience:
            data.yearsOfExperience === "" || data.yearsOfExperience === null
                ? null
                : Number(data.yearsOfExperience),
        keySkills: data.keySkills || "",
        preferredTopK:
            data.topK === "" || data.topK === null ? 8 : Number(data.topK),
    };

    const response = await api.post("/api/users/profile", payload);
    return response.data;
}

/*
  Upload resume + profile data to the recommendation backend.
*/
export async function uploadResumeAndGetRecommendations(payload) {
    const formData = new FormData();

    if (payload.file) {
        formData.append("file", payload.file);
    }

    formData.append("firstName", payload.firstName || "");
    formData.append("lastName", payload.lastName || "");
    formData.append("pronouns", payload.pronouns || "");
    formData.append("location", payload.location || "");
    formData.append("targetRole", payload.targetRole || "");
    formData.append("yearsOfExperience", payload.yearsOfExperience || "");
    formData.append("keySkills", payload.keySkills || "");

    const topK = payload.topK || 8;

    try {
        const response = await api.post(
            `/api/recommendations/upload-resume?topK=${topK}`,
            formData,
            {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            }
        );

        return response.data;
    } catch (error) {
        console.error("Upload error:", error);
        console.error("Response data:", error?.response?.data);
        console.error("Status:", error?.response?.status);
        throw error;
    }
}

export default api;
