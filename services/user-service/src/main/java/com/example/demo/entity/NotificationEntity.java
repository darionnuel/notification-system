package com.example.demo.entity;

import jakarta.persistence.*;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name="notifications")
public class NotificationEntity {
    @Id
    @GeneratedValue
    private UUID notificationId;

    @Column(unique=true)
    private String requestId;

    private UUID userId;
    private String notificationType;
    private String templateCode;

    @Column(columnDefinition = "jsonb")
    private String variables; // store JSON as string or use Jackson + @Convert

    private String status;
    private Integer attempts;
    private String lastError;

    @Column(columnDefinition = "jsonb")
    private String metadata;

    private OffsetDateTime createdAt;
    private OffsetDateTime updatedAt;

    public NotificationEntity(UUID notificationId, String requestId, UUID userId, String notificationType, String templateCode, String variables, String status, Integer attempts, String lastError, String metadata, OffsetDateTime createdAt, OffsetDateTime updatedAt) {
        this.notificationId = notificationId;
        this.requestId = requestId;
        this.userId = userId;
        this.notificationType = notificationType;
        this.templateCode = templateCode;
        this.variables = variables;
        this.status = status;
        this.attempts = attempts;
        this.lastError = lastError;
        this.metadata = metadata;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public NotificationEntity() {
    }

    public UUID getNotificationId() {
        return notificationId;
    }

    public void setNotificationId(UUID notificationId) {
        this.notificationId = notificationId;
    }

    public String getRequestId() {
        return requestId;
    }

    public void setRequestId(String requestId) {
        this.requestId = requestId;
    }

    public UUID getUserId() {
        return userId;
    }

    public void setUserId(UUID userId) {
        this.userId = userId;
    }

    public String getNotificationType() {
        return notificationType;
    }

    public void setNotificationType(String notificationType) {
        this.notificationType = notificationType;
    }

    public String getTemplateCode() {
        return templateCode;
    }

    public void setTemplateCode(String templateCode) {
        this.templateCode = templateCode;
    }

    public String getVariables() {
        return variables;
    }

    public void setVariables(String variables) {
        this.variables = variables;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public Integer getAttempts() {
        return attempts;
    }

    public void setAttempts(Integer attempts) {
        this.attempts = attempts;
    }

    public String getLastError() {
        return lastError;
    }

    public void setLastError(String lastError) {
        this.lastError = lastError;
    }

    public String getMetadata() {
        return metadata;
    }

    public void setMetadata(String metadata) {
        this.metadata = metadata;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(OffsetDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public OffsetDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(OffsetDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }


    // getters/setters, @PrePersist / @PreUpdate members to set timestamps
}
