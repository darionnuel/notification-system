package com.example.demo.controller;

import com.example.demo.dto.*;
import com.example.demo.entity.NotificationPreference;
import com.example.demo.entity.User;
import com.example.demo.repository.UserRepository;
import com.example.demo.security.JwtService;
import com.example.demo.service.UserService;

import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    private final UserService userService;
    private final UserRepository userRepository;
    private final JwtService jwtService;

    public UserController(UserService userService, UserRepository userRepository, JwtService jwtService) {
        this.userService = userService;
        this.userRepository = userRepository;
        this.jwtService = jwtService;
    }

    @PostMapping
    public ResponseEntity<ApiResponse<UserResponseDTO>> createUser(@RequestBody @Valid UserRequest request) {
        try {
            // Convert UserRequest to User entity
            User user = new User();
            user.setName(request.getName());
            user.setEmail(request.getEmail());
            user.setPassword(request.getPassword());
            user.setPushToken(request.getPush_token());

            UserResponseDTO response = userService.createUser(user);

            ApiResponse<UserResponseDTO> apiResponse = new ApiResponse<>(
                    true,
                    response,
                    null,
                    "User created successfully",
                    null
            );

            return ResponseEntity.status(HttpStatus.CREATED).body(apiResponse);
        } catch (Exception e) {
            ApiResponse<UserResponseDTO> errorResponse = new ApiResponse<>(
                    false,
                    null,
                    e.getMessage(),
                    "Failed to create user",
                    null
            );
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse);
        }
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<User>> getUser(@PathVariable UUID id) {
        return userService.getUserById(id)
                .map(user -> {
                    ApiResponse<User> response = new ApiResponse<>(
                            true,
                            user,
                            null,
                            "User retrieved successfully",
                            null
                    );
                    return ResponseEntity.ok(response);
                })
                .orElseGet(() -> {
                    ApiResponse<User> response = new ApiResponse<>(
                            false,
                            null,
                            "User not found",
                            "User not found",
                            null
                    );
                    return ResponseEntity.status(HttpStatus.NOT_FOUND).body(response);
                });
    }

    @PutMapping("/{id}/preferences")
    public ResponseEntity<ApiResponse<NotificationPreference>> updatePreferences(
            @PathVariable UUID id,
            @RequestBody NotificationPreference pref
    ) {
        try {
            NotificationPreference updated = userService.updatePreferences(id, pref);
            ApiResponse<NotificationPreference> response = new ApiResponse<>(
                    true,
                    updated,
                    null,
                    "Preferences updated successfully",
                    null
            );
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            ApiResponse<NotificationPreference> errorResponse = new ApiResponse<>(
                    false,
                    null,
                    e.getMessage(),
                    "Failed to update preferences",
                    null
            );
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse);
        }
    }

    @PostMapping("/login")
    public ResponseEntity<ApiResponse<Map<String, String>>> login(@RequestBody @Valid LoginRequest request) {
        try {
            User user = userService.authenticate(request.getEmail(), request.getPassword());
            String token = jwtService.generateToken(user.getEmail());

            Map<String, String> data = Map.of("token", token);
            ApiResponse<Map<String, String>> response = new ApiResponse<>(
                    true,
                    data,
                    null,
                    "Login successful",
                    null
            );

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            ApiResponse<Map<String, String>> errorResponse = new ApiResponse<>(
                    false,
                    null,
                    e.getMessage(),
                    "Login failed",
                    null
            );
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(errorResponse);
        }
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        return ResponseEntity.ok(Map.of("status", "healthy", "service", "user-service"));
    }

    @GetMapping
    public ResponseEntity<ApiResponse<List<User>>> getAllUsers(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int limit
    ) {
        Page<User> users = userRepository.findAll(PageRequest.of(page, limit));

        PaginationMeta meta = new PaginationMeta(
                users.getTotalElements(),
                limit,
                page,
                users.getTotalPages(),
                users.hasNext(),
                users.hasPrevious()
        );

        ApiResponse<List<User>> response = new ApiResponse<>(
                true,
                users.getContent(),
                null,
                "Users fetched successfully",
                meta
        );

        return ResponseEntity.ok(response);
    }
}

//package com.example.demo.controller;
//
//import com.example.demo.dto.ApiResponse;
//import com.example.demo.dto.LoginRequest;
//import com.example.demo.dto.PaginationMeta;
//import com.example.demo.dto.UserResponseDTO;
//import com.example.demo.entity.NotificationPreference;
//import com.example.demo.entity.User;
//import com.example.demo.repository.UserRepository;
//import com.example.demo.security.JwtService;
//import com.example.demo.service.UserService;
//
//import jakarta.validation.Valid;
//import org.springframework.data.domain.Page;
//import org.springframework.data.domain.PageRequest;
//import org.springframework.http.ResponseEntity;
//import org.springframework.web.bind.annotation.*;
//
//import java.util.List;
//import java.util.Map;
//import java.util.UUID;
//
//@RestController
//@RequestMapping("/api/v1/users")
////@RequiredArgsConstructor
//public class UserController {
//
//    private final UserService userService;
//    private final UserRepository userRepository;
//    private final JwtService jwtService;
//
//    public UserController(UserService userService, UserRepository userRepository, JwtService jwtService) {
//        this.userService = userService;
//        this.userRepository = userRepository;
//        this.jwtService = jwtService;
//    }
//
////    @PostMapping
////    public ResponseEntity<User> createUser(@RequestBody User user) {
////        return ResponseEntity.ok(userService.createUser(user));
////    }
//
//    @PostMapping
//    public ResponseEntity<UserResponseDTO> createUser(@RequestBody User user) {
//        UserResponseDTO response = userService.createUser(user);
//        return ResponseEntity.ok(response);
//    }
//
//    @GetMapping("/{id}")
//    public ResponseEntity<User> getUser(@PathVariable UUID id) {
//        return userService.getUserById(id)
//                .map(ResponseEntity::ok)
//                .orElse(ResponseEntity.notFound().build());
//    }
//
//    @PutMapping("/{id}/preferences")
//    public ResponseEntity<NotificationPreference> updatePreferences(
//            @PathVariable UUID id,
//            @RequestBody NotificationPreference pref
//    ) {
//        return ResponseEntity.ok(userService.updatePreferences(id, pref));
//    }
//
//    @PostMapping("/login")
//    public ResponseEntity<ApiResponse<Map<String, String>>> login(@RequestBody @Valid LoginRequest request) {
//        User user = userService.authenticate(request.getEmail(), request.getPassword());
//        String token = jwtService.generateToken(user.getEmail());
//
//        Map<String, String> data = Map.of("token", token);
//        ApiResponse<Map<String, String>> response = new ApiResponse<>(true, data, null, "Login successful", null);
//
//        return ResponseEntity.ok(response);
//    }
//
//
//    @GetMapping("/health")
//    public ResponseEntity<String> health() {
//        return ResponseEntity.ok("User Service is healthy ✅");
//    }
//
//
//    @GetMapping
//    public ResponseEntity<ApiResponse<List<User>>> getAllUsers(
//            @RequestParam(defaultValue = "0") int page,
//            @RequestParam(defaultValue = "10") int limit
//    ) {
//        Page<User> users = userRepository.findAll(PageRequest.of(page, limit));
//
//        PaginationMeta meta = new PaginationMeta(
//                users.getTotalElements(),
//                limit,
//                page,
//                users.getTotalPages(),
//                users.hasNext(),
//                users.hasPrevious()
//        );
//
//        ApiResponse<List<User>> response = new ApiResponse<>(
//                true,
//                users.getContent(),
//                null,
//                "Users fetched successfully",
//                meta
//        );
//
//        return ResponseEntity.ok(response);
//    }
//
//}
//
