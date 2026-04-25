package com.example.jobplatform.dto;

/**
 * Request body for saving user profile information.
 */
public class UserProfileRequest {

    private String email;
    private String location;
    private String targetRole;
    private Integer yearsOfExperience;
    private String keySkills;
    private Integer preferredTopK;

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getLocation() {
        return location;
    }

    public void setLocation(String location) {
        this.location = location;
    }

    public String getTargetRole() {
        return targetRole;
    }

    public void setTargetRole(String targetRole) {
        this.targetRole = targetRole;
    }

    public Integer getYearsOfExperience() {
        return yearsOfExperience;
    }

    public void setYearsOfExperience(Integer yearsOfExperience) {
        this.yearsOfExperience = yearsOfExperience;
    }

    public String getKeySkills() {
        return keySkills;
    }

    public void setKeySkills(String keySkills) {
        this.keySkills = keySkills;
    }

    public Integer getPreferredTopK() {
        return preferredTopK;
    }

    public void setPreferredTopK(Integer preferredTopK) {
        this.preferredTopK = preferredTopK;
    }
}
