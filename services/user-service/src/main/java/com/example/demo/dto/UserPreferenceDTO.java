package com.example.demo.dto;


public class UserPreferenceDTO {

    private Boolean email_enabled;
    private Boolean push_enabled;
    private String language;

    public UserPreferenceDTO(Boolean emailEnabled, Boolean pushEnabled, String language) {
        this.email_enabled = emailEnabled;
        this.push_enabled = pushEnabled;
        this.language = language;
    }

    public UserPreferenceDTO() {
    }

    public Boolean getEmail_enabled() { return email_enabled; }
    public void setEmail_enabled(Boolean email_enabled) { this.email_enabled = email_enabled; }

    public Boolean getPush_enabled() { return push_enabled; }
    public void setPush_enabled(Boolean push_enabled) { this.push_enabled = push_enabled; }

    public String getLanguage() { return language; }
    public void setLanguage(String language) { this.language = language; }
}
