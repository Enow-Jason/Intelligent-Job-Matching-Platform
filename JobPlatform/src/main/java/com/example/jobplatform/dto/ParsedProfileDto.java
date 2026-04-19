package com.example.jobplatform.dto;

import java.util.List;

/**
 * Represents the lightweight parsed resume profile
 * returned by the FastAPI upload endpoint.
 */
public class ParsedProfileDto {

    private int experience_years;
    private List<String> extracted_skills;
    private String inferred_role;
    private String education;

    public int getExperience_years() {
        return experience_years;
    }

    public void setExperience_years(int experience_years) {
        this.experience_years = experience_years;
    }

    public List<String> getExtracted_skills() {
        return extracted_skills;
    }

    public void setExtracted_skills(List<String> extracted_skills) {
        this.extracted_skills = extracted_skills;
    }

    public String getInferred_role() {
        return inferred_role;
    }

    public void setInferred_role(String inferred_role) {
        this.inferred_role = inferred_role;
    }

    public String getEducation() {
        return education;
    }

    public void setEducation(String education) {
        this.education = education;
    }
}
