import { useState } from "react";
import { uploadResumeAndGetRecommendations } from "../services/api";

/*
  Custom hook to manage recommendation fetch lifecycle:
  - loading
  - error
  - response data
*/
export default function useRecommendations() {
    const [data, setData] = useState(null);
    const [recommendations, setRecommendations] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const fetchRecommendations = async (payload) => {
        try {
            setLoading(true);
            setError("");

            const result = await uploadResumeAndGetRecommendations(payload);

            setData(result);
            setRecommendations(result.results || []);
            return result;
        } catch (err) {
            setError(
                err?.response?.data?.message ||
                err?.message ||
                "Something went wrong while generating recommendations."
            );
            throw err;
        } finally {
            setLoading(false);
        }
    };

    return {
        data,
        recommendations,
        loading,
        error,
        fetchRecommendations,
    };
}
