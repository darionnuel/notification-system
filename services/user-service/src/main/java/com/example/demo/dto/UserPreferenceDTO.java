package com.example.demo.dto;


public class UserPreferenceDTO {
    private boolean email;
    private boolean push;

    public UserPreferenceDTO(boolean email, boolean push) {
        this.email = email;
        this.push = push;
    }

    public boolean isEmail() {
        return email;
    }

    public void setEmail(boolean email) {
        this.email = email;
    }

    public boolean isPush() {
        return push;
    }

    public void setPush(boolean push) {
        this.push = push;
    }
}
