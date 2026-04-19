package com.example.jobplatform.dto;

import java.util.List;

/**
 * Full response returned by the FastAPI upload endpoint.
 */
public class AiUploadResponse {

    private String filename;
    private ParsedProfileDto parsed_profile;
    private List<JobRecommendationDto> results;

    public String getFilename() {
        return filename;
    }

    public void setFilename(String filename) {
        this.filename = filename;
    }

    public ParsedProfileDto getParsed_profile() {
        return parsed_profile;
    }

    public void setParsed_profile(ParsedProfileDto parsed_profile) {
        this.parsed_profile = parsed_profile;
    }

    public List<JobRecommendationDto> getResults() {
        return results;
    }

    public void setResults(List<JobRecommendationDto> results) {
        this.results = results;
    }
}
