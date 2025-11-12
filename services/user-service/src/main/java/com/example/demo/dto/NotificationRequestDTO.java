package com.example.demo.dto;

import java.util.Map;
import java.util.UUID;

public class NotificationRequestDTO {
    private String notification_type; // "email" | "push"
    private UUID user_id;
    private String template_code;
    private Map<String, Object> variables;
    private String request_id;       // idempotency key
    private Integer priority;
    private Map<String, Object> metadata;

    public NotificationRequestDTO(String notification_type, UUID user_id, String template_code, Map<String, Object> variables, String request_id, Integer priority, Map<String, Object> metadata) {
        this.notification_type = notification_type;
        this.user_id = user_id;
        this.template_code = template_code;
        this.variables = variables;
        this.request_id = request_id;
        this.priority = priority;
        this.metadata = metadata;
    }

    public String getNotification_type() {
        return notification_type;
    }

    public void setNotification_type(String notification_type) {
        this.notification_type = notification_type;
    }

    public UUID getUser_id() {
        return user_id;
    }

    public void setUser_id(UUID user_id) {
        this.user_id = user_id;
    }

    public String getTemplate_code() {
        return template_code;
    }

    public void setTemplate_code(String template_code) {
        this.template_code = template_code;
    }

    public Map<String, Object> getVariables() {
        return variables;
    }

    public void setVariables(Map<String, Object> variables) {
        this.variables = variables;
    }

    public String getRequest_id() {
        return request_id;
    }

    public void setRequest_id(String request_id) {
        this.request_id = request_id;
    }

    public Integer getPriority() {
        return priority;
    }

    public void setPriority(Integer priority) {
        this.priority = priority;
    }

    public Map<String, Object> getMetadata() {
        return metadata;
    }

    public void setMetadata(Map<String, Object> metadata) {
        this.metadata = metadata;
    }

    // getters/setters
}

