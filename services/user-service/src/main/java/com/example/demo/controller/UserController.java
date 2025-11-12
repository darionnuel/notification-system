package com.example.demo.controller;

import com.example.demo.dto.ApiResponse;
import com.example.demo.dto.LoginRequest;
import com.example.demo.dto.PaginationMeta;
import com.example.demo.dto.UserResponseDTO;
import com.example.demo.entity.NotificationPreference;
import com.example.demo.entity.User;
import com.example.demo.repository.UserRepository;
import com.example.demo.security.JwtService;
import com.example.demo.service.UserService;

import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/users")
//@RequiredArgsConstructor
public class UserController {

    private final UserService userService;
    private final UserRepository userRepository;
    private final JwtService jwtService;

    public UserController(UserService userService, UserRepository userRepository, JwtService jwtService) {
        this.userService = userService;
        this.userRepository = userRepository;
        this.jwtService = jwtService;
    }

//    @PostMapping
//    public ResponseEntity<User> createUser(@RequestBody User user) {
//        return ResponseEntity.ok(userService.createUser(user));
//    }

    @PostMapping
    public ResponseEntity<UserResponseDTO> createUser(@RequestBody User user) {
        UserResponseDTO response = userService.createUser(user);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/{id}")
    public ResponseEntity<User> getUser(@PathVariable UUID id) {
        return userService.getUserById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PutMapping("/{id}/preferences")
    public ResponseEntity<NotificationPreference> updatePreferences(
            @PathVariable UUID id,
            @RequestBody NotificationPreference pref
    ) {
        return ResponseEntity.ok(userService.updatePreferences(id, pref));
    }

    @PostMapping("/login")
    public ResponseEntity<ApiResponse<Map<String, String>>> login(@RequestBody @Valid LoginRequest request) {
        User user = userService.authenticate(request.getEmail(), request.getPassword());
        String token = jwtService.generateToken(user.getEmail());

        Map<String, String> data = Map.of("token", token);
        ApiResponse<Map<String, String>> response = new ApiResponse<>(true, data, null, "Login successful", null);

        return ResponseEntity.ok(response);
    }


    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("User Service is healthy ✅");
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

