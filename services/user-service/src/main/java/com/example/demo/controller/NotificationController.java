package com.example.demo.controller;

import com.example.demo.dto.ApiResponse;
import com.example.demo.dto.NotificationRequestDTO;
import com.example.demo.dto.NotificationStatusRequestDTO;
import com.example.demo.service.NotificationService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1")
public class NotificationController {
    private final NotificationService notificationService;

    public NotificationController(NotificationService notificationService) {
        this.notificationService = notificationService;
    }

    @PostMapping("/notifications")
    public ResponseEntity<ApiResponse<Map<String,Object>>> create(@RequestBody @Valid NotificationRequestDTO req) {
        ApiResponse<Map<String,Object>> resp = notificationService.createNotification(req);
        return ResponseEntity.status(resp.isSuccess()? HttpStatus.OK:HttpStatus.BAD_REQUEST).body(resp);
    }

    @PostMapping("/notifications/{notification_id}/status")
    public ResponseEntity<ApiResponse<Void>> statusUpdate(
            @PathVariable("notification_id") UUID notificationId,
            @RequestBody NotificationStatusRequestDTO req) {
        // ensure body.notification_id matches path variable or ignore body field
        req.setNotification_id(notificationId.toString());
        ApiResponse<Void> resp = notificationService.updateStatus(req);
        return ResponseEntity.ok(resp);
    }
}
