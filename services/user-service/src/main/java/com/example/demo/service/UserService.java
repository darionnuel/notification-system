package com.example.demo.service;


import com.example.demo.dto.UserPreferenceDTO;
import com.example.demo.dto.UserResponseDTO;
import com.example.demo.entity.NotificationPreference;
import com.example.demo.entity.User;
import com.example.demo.repository.NotificationPreferenceRepository;
import com.example.demo.repository.UserRepository;
import org.springframework.stereotype.Service;

import java.util.Optional;
import java.util.UUID;

@Service
//@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    private final NotificationPreferenceRepository preferenceRepository;

    public UserService(UserRepository userRepository, NotificationPreferenceRepository preferenceRepository) {
        this.userRepository = userRepository;
        this.preferenceRepository = preferenceRepository;
    }

    public UserResponseDTO createUser(User user) {
//        user.setPassword(passwordEncoder.encode(user.getPassword()));

        NotificationPreference pref = new NotificationPreference();
        pref.setEmailEnabled(true);
        pref.setPushEnabled(false);
        pref.setLanguage("en");
        pref.setUser(user);

        user.setPreference(pref);
        User saved = userRepository.save(user);

        return mapToDto(saved);
    }


    private UserResponseDTO mapToDto(User user) {
        UserPreferenceDTO prefDto = null;
        if (user.getPreference() != null) {
            prefDto = UserPreferenceDTO.builder()
                    .email(user.getPreference().getEmailEnabled())
                    .push(user.getPreference().getPushEnabled())
                    .build();
        }

        return UserResponseDTO.builder()
                .email(user.getEmail())
                .push_token(user.getPushToken())
                .preferences(prefDto)
                .build();
    }

    public Optional<User> getUserById(UUID id) {
        return userRepository.findById(id);
    }

    public User authenticate(String email, String password) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("Invalid email or password"));
        if (!user.getPassword().equals(password)) {
            throw new RuntimeException("Invalid email or password");
        }
        return user;
    }


    public NotificationPreference updatePreferences(UUID userId, NotificationPreference pref) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));
        pref.setUser(user);
//        //
//        user.setPreference(pref);
//        userRepository.save(user);

        return preferenceRepository.save(pref);
    }
}

