package com.example.jobplatform.dto;

import java.util.List;

/**
 * Represents one recommended job returned by the AI service.
 */
public class JobRecommendationDto {

    private String job_id;
    private String job_title;
    private String role;
    private String salary_range;
    private String company_name;
    private String location;
    private String country;
    private String work_type;
    private String job_portal;
    private String experience;
    private String qualifications;
    private String description_snippet;
    private String job_description;
    private double semantic_score;
    private double final_score;
    private List<String> matched_skills;
    private List<String> missing_skills_top10;

    // New personalised explanation field
    private List<String> why_recommended_bullets;

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

    public String getRole() {
        return role;
    }

    public void setRole(String role) {
        this.role = role;
    }

    public String getSalary_range() {
        return salary_range;
    }

    public void setSalary_range(String salary_range) {
        this.salary_range = salary_range;
    }

    public String getCompany_name() {
        return company_name;
    }

    public void setCompany_name(String company_name) {
        this.company_name = company_name;
    }

    public String getLocation() {
        return location;
    }

    public void setLocation(String location) {
        this.location = location;
    }

    public String getCountry() {
        return country;
    }

    public void setCountry(String country) {
        this.country = country;
    }

    public String getWork_type() {
        return work_type;
    }

    public void setWork_type(String work_type) {
        this.work_type = work_type;
    }

    public String getJob_portal() {
        return job_portal;
    }

    public void setJob_portal(String job_portal) {
        this.job_portal = job_portal;
    }

    public String getExperience() {
        return experience;
    }

    public void setExperience(String experience) {
        this.experience = experience;
    }

    public String getQualifications() {
        return qualifications;
    }

    public void setQualifications(String qualifications) {
        this.qualifications = qualifications;
    }

    public String getDescription_snippet() {
        return description_snippet;
    }

    public void setDescription_snippet(String description_snippet) {
        this.description_snippet = description_snippet;
    }

    public String getJob_description() {
        return job_description;
    }

    public void setJob_description(String job_description) {
        this.job_description = job_description;
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

    public List<String> getWhy_recommended_bullets() {
        return why_recommended_bullets;
    }

    public void setWhy_recommended_bullets(List<String> why_recommended_bullets) {
        this.why_recommended_bullets = why_recommended_bullets;
    }
}
