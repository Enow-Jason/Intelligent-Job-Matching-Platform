package com.example.jobplatform.dto;

import java.util.List;

/**
 * Represents one recommended job returned by the AI service.
 */
public class JobRecommendationDto {

    private String job_id;
    private String job_title;
    private double semantic_score;
    private double final_score;
    private List<String> matched_skills;
    private List<String> missing_skills_top10;

    public String getJob_id() {
        return job_id;
    }

    public void setJob_id(String job_id) {
        this.job_id = job_id;
    }

    public String getJob_title() {
        return job_title;
    }

    public void setJob_title(String job_title) {
        this.job_title = job_title;
    }

    public double getSemantic_score() {
        return semantic_score;
    }

    public void setSemantic_score(double semantic_score) {
        this.semantic_score = semantic_score;
    }

    public double getFinal_score() {
        return final_score;
    }

    public void setFinal_score(double final_score) {
        this.final_score = final_score;
    }

    public List<String> getMatched_skills() {
        return matched_skills;
    }

    public void setMatched_skills(List<String> matched_skills) {
        this.matched_skills = matched_skills;
    }

    public List<String> getMissing_skills_top10() {
        return missing_skills_top10;
    }

    public void setMissing_skills_top10(List<String> missing_skills_top10) {
        this.missing_skills_top10 = missing_skills_top10;
    }
}
