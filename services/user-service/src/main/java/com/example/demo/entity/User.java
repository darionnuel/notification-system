package com.example.demo.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity

@Table(name = "users")
@Builder
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private UUID id;

    @Column(nullable = true)
    private String name;


    @Column(unique = true, nullable = false)
    private String email;

    private String pushToken;

//    @JsonIgnore
    private String password;

    private LocalDateTime createdAt = LocalDateTime.now();

    @OneToOne(mappedBy = "user", cascade = CascadeType.ALL)
    private NotificationPreference preference;

    public User() {
    }

    public User(UUID id, String name, String email, String pushToken, String password, LocalDateTime createdAt, NotificationPreference preference) {
        this.id = id;
        this.name = name;
        this.email = email;
        this.pushToken = pushToken;
        this.password = password;
        this.createdAt = createdAt;
        this.preference = preference;
    }

    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
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

    public String getPushToken() {
        return pushToken;
    }

    public void setPushToken(String pushToken) {
        this.pushToken = pushToken;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public NotificationPreference getPreference() {
        return preference;
    }

    public void setPreference(NotificationPreference preference) {
        this.preference = preference;
    }
}

