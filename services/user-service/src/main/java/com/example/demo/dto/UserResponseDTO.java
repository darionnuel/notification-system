package com.example.demo.dto;


public class UserResponseDTO {

    private String name;
    private String email;
    private String push_token;

    private UserPreferenceDTO preferences;
    private String created_at;

    public UserResponseDTO(String name, String email, String push_token, UserPreferenceDTO preferences, String created_at) {
        this.name = name;
        this.email = email;
        this.push_token = push_token;
        this.preferences = preferences;
        this.created_at = created_at;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPush_token() {
        return push_token;
    }

    public void setPush_token(String push_token) {
        this.push_token = push_token;
    }

    public UserPreferenceDTO getPreferences() {
        return preferences;
    }

    public void setPreferences(UserPreferenceDTO preferences) {
        this.preferences = preferences;
    }

    public String getCreated_at() {
        return created_at;
    }

    public void setCreated_at(String created_at) {
        this.created_at = created_at;
    }
}
