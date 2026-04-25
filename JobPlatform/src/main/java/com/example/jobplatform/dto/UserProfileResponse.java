package com.example.jobplatform.dto;

/**
 * Response DTO for returning saved user + profile information.
 */
public class UserProfileResponse {

    private String firstName;
    private String lastName;
    private String pronouns;
    private String email;
    private String location;
    private String targetRole;
    private Integer yearsOfExperience;
    private String keySkills;
    private Integer preferredTopK;

    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }

    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }

    public String getPronouns() {
        return pronouns;
    }

    public void setPronouns(String pronouns) {
        this.pronouns = pronouns;
    }

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
