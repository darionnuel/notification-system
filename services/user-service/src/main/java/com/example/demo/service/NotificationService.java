package com.example.demo.service;

import com.example.demo.config.NotificationPublisher;
import com.example.demo.dto.ApiResponse;
import com.example.demo.dto.NotificationRequestDTO;
import com.example.demo.dto.NotificationStatusRequestDTO;
import com.example.demo.entity.NotificationEntity;
import com.example.demo.entity.NotificationPreference;
import com.example.demo.entity.User;
import com.example.demo.repository.NotificationRepository;
import com.example.demo.repository.UserRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Service
public class NotificationService {

    private final NotificationRepository notificationRepository;
    private final UserRepository userRepository; // to fetch preferences & user contact
    private final NotificationPublisher publisher;

    private final ObjectMapper objectMapper;

    public NotificationService(NotificationRepository notificationRepository, UserRepository userRepository, NotificationPublisher publisher, ObjectMapper objectMapper) {
        this.notificationRepository = notificationRepository;
        this.userRepository = userRepository;
        this.publisher = publisher;
        this.objectMapper = objectMapper;
    }

    // create/send notification
    @Transactional
    public ApiResponse<Map<String, Object>> createNotification(NotificationRequestDTO req) {
        // 1. idempotency: check request_id
        if (req.getRequest_id() != null) {
            Optional<NotificationEntity> existing = notificationRepository.findByRequestId(req.getRequest_id());
            if (existing.isPresent()) {
                Map<String, Object> data = Map.of("notification_id", existing.get().getNotificationId());
                return new ApiResponse<>(true, data, null, "already_queued", null);
            }
        }

        // 2. validate user exists
        User user = userRepository.findById(req.getUser_id())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.BAD_REQUEST, "user_not_found"));

        // 3. check user preferences
        NotificationPreference pref = user.getPreference();
        if ("email".equalsIgnoreCase(req.getNotification_type()) && (pref == null || !Boolean.TRUE.equals(pref.getEmailEnabled()))) {
            return new ApiResponse<>(false, null, null, "user_disabled_email", null);
        }
        if ("push".equalsIgnoreCase(req.getNotification_type()) && (pref == null || !Boolean.TRUE.equals(pref.getPushEnabled()))) {
            return new ApiResponse<>(false, null, null, "user_disabled_push", null);
        }

        // 4. persist notification (status = queued)
        NotificationEntity e = new NotificationEntity();
        e.setRequestId(req.getRequest_id());
        e.setUserId(req.getUser_id());
        e.setNotificationType(req.getNotification_type());
        e.setTemplateCode(req.getTemplate_code());
        e.setVariables(convertMapToJson(req.getVariables()));
        e.setStatus("queued");
        e.setAttempts(0);
        e.setMetadata(convertMapToJson(req.getMetadata()));
        e.setCreatedAt(OffsetDateTime.now());
        e.setUpdatedAt(OffsetDateTime.now());
        NotificationEntity saved = notificationRepository.save(e);

        // 5. publish to queue (delegated)
        try {
            publisher.publish("notification-exchange", "notification-routing-key", req);
        } catch (Exception ex) {
            // optionally set status=failed or keep queued for retry
            saved.setStatus("failed");
            saved.setLastError(ex.getMessage());
            notificationRepository.save(saved);
            return new ApiResponse<>(false, null, ex.getMessage(), "publish_failed", null);
        }

        Map<String, Object> respData = Map.of("notification_id", saved.getNotificationId());
        return new ApiResponse<>(true, respData, null, "notification_queued", null);
    }

    // status update endpoint
    @Transactional
    public ApiResponse<Void> updateStatus(NotificationStatusRequestDTO req) {
        UUID notificationId = UUID.fromString(req.getNotification_id());
        NotificationEntity e = notificationRepository.findById(notificationId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "notification_not_found"));

        // idempotency check: if already 'delivered' and incoming is 'delivered' -> noop
        if ("delivered".equalsIgnoreCase(e.getStatus()) && "delivered".equalsIgnoreCase(req.getStatus())) {
            return new ApiResponse<>(true, null, null, "already_delivered", null);
        }

        e.setStatus(req.getStatus());
        e.setLastError(req.getError());
        e.setAttempts((e.getAttempts() == null ? 0 : e.getAttempts()) + ("failed".equalsIgnoreCase(req.getStatus()) ? 1 : 0));
        e.setUpdatedAt(OffsetDateTime.now());
        notificationRepository.save(e);

        return new ApiResponse<>(true, null, null, "status_updated", null);
    }

    // helper converter (use Jackson in real code)
    private String convertMapToJson(Map<String, Object> map) {
        if (map == null) return "{}";
        try {
            return objectMapper.writeValueAsString(map);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Failed to convert map to JSON", e);
        }
    }

}

