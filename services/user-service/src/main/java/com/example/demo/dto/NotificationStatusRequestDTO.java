package com.example.demo.dto;

public class NotificationStatusRequestDTO {
    private String notification_id;
    private String status; // delivered | pending | failed
    private String error;  // optional
    private String timestamp; // optional
    // getters/setters


    public NotificationStatusRequestDTO(String notification_id, String status, String error, String timestamp) {
        this.notification_id = notification_id;
        this.status = status;
        this.error = error;
        this.timestamp = timestamp;
    }

    public String getNotification_id() {
        return notification_id;
    }

    public void setNotification_id(String notification_id) {
        this.notification_id = notification_id;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getError() {
        return error;
    }

    public void setError(String error) {
        this.error = error;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }
}


