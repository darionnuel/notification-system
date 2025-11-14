package com.example.demo.dto;


import java.util.UUID;

public class UserResponseDTO {

    private UUID id;
    private String name;
    private String email;
    private String push_token;
    private UserPreferenceDTO preferences;

    public UserResponseDTO() {
    }

    public UserResponseDTO(UUID id, String name, String email, String push_token, UserPreferenceDTO preferences) {
        this.id = id;
        this.name = name;
        this.email = email;
        this.push_token = push_token;
        this.preferences = preferences;
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getPush_token() { return push_token; }
    public void setPush_token(String push_token) { this.push_token = push_token; }

    public UserPreferenceDTO getPreferences() { return preferences; }
    public void setPreferences(UserPreferenceDTO preferences) { this.preferences = preferences; }
}
