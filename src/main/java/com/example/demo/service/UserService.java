package com.example.demo.service;


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

    public User createUser(User user) {
        return userRepository.save(user);
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

