package com.example.jobplatform.service;

import com.example.jobplatform.dto.ChangePasswordRequest;
import com.example.jobplatform.dto.SignInRequest;
import com.example.jobplatform.dto.SignUpRequest;
import com.example.jobplatform.dto.UserProfileRequest;
import com.example.jobplatform.dto.UserProfileResponse;
import com.example.jobplatform.entity.User;
import com.example.jobplatform.entity.UserProfile;
import com.example.jobplatform.repository.UserProfileRepository;
import com.example.jobplatform.repository.UserRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Service layer for:
 * - creating users
 * - authenticating users
 * - saving/loading profiles
 * - changing local account passwords
 */
@Service
public class UserProfileService {

    private final UserRepository userRepository;
    private final UserProfileRepository userProfileRepository;
    private final PasswordEncoder passwordEncoder;

    public UserProfileService(
            UserRepository userRepository,
            UserProfileRepository userProfileRepository,
            PasswordEncoder passwordEncoder
    ) {
        this.userRepository = userRepository;
        this.userProfileRepository = userProfileRepository;
        this.passwordEncoder = passwordEncoder;
    }

    /**
     * Create a new user and hash their password before saving.
     */
    @Transactional
    public UserProfileResponse createUser(SignUpRequest request) {
        if (userRepository.findByEmail(request.getEmail()).isPresent()) {
            throw new RuntimeException("An account with this email already exists.");
        }

        User user = new User();
        user.setFirstName(request.getFirstName());
        user.setLastName(request.getLastName());
        user.setPronouns(request.getPronouns());
        user.setEmail(request.getEmail());

        // Hash password before saving
        user.setPassword(passwordEncoder.encode(request.getPassword()));

        User savedUser = userRepository.save(user);

        // Create default profile for new user
        UserProfile profile = new UserProfile();
        profile.setUser(savedUser);
        profile.setPreferredTopK(8);

        UserProfile savedProfile = userProfileRepository.save(profile);

        return mapToResponse(savedUser, savedProfile);
    }

    /**
     * Real password-based sign-in.
     */
    @Transactional(readOnly = true)
    public UserProfileResponse authenticateUser(SignInRequest request) {
        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new RuntimeException("Invalid email or password."));

        boolean matches = passwordEncoder.matches(request.getPassword(), user.getPassword());

        if (!matches) {
            throw new RuntimeException("Invalid email or password.");
        }

        UserProfile profile = userProfileRepository.findByUserId(user.getId())
                .orElseGet(() -> {
                    UserProfile p = new UserProfile();
                    p.setUser(user);
                    p.setPreferredTopK(8);
                    return p;
                });

        return mapToResponse(user, profile);
    }

    /**
     * Change a local account password.
     *
     * Steps:
     * 1. load user by email
     * 2. verify current password
     * 3. hash and save new password
     */
    @Transactional
    public void changePassword(ChangePasswordRequest request) {
        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new RuntimeException("User not found."));

        boolean matches = passwordEncoder.matches(request.getCurrentPassword(), user.getPassword());

        if (!matches) {
            throw new RuntimeException("Current password is incorrect.");
        }

        if (request.getNewPassword() == null || request.getNewPassword().trim().length() < 8) {
            throw new RuntimeException("New password must be at least 8 characters.");
        }

        user.setPassword(passwordEncoder.encode(request.getNewPassword()));
        userRepository.save(user);
    }

    /**
     * Save recommendation/profile fields for a user.
     */
    @Transactional
    public UserProfileResponse saveProfile(UserProfileRequest request) {
        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new RuntimeException("User not found."));

        UserProfile profile = userProfileRepository.findByUserId(user.getId())
                .orElseGet(() -> {
                    UserProfile p = new UserProfile();
                    p.setUser(user);
                    return p;
                });

        profile.setLocation(request.getLocation());
        profile.setTargetRole(request.getTargetRole());
        profile.setYearsOfExperience(request.getYearsOfExperience());
        profile.setKeySkills(request.getKeySkills());
        profile.setPreferredTopK(request.getPreferredTopK());

        UserProfile savedProfile = userProfileRepository.save(profile);

        return mapToResponse(user, savedProfile);
    }

    /**
     * Load a profile by email.
     */
    @Transactional(readOnly = true)
    public UserProfileResponse getProfileByEmail(String email) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("User not found."));

        UserProfile profile = userProfileRepository.findByUserId(user.getId())
                .orElseGet(() -> {
                    UserProfile p = new UserProfile();
                    p.setUser(user);
                    p.setPreferredTopK(8);
                    return p;
                });

        return mapToResponse(user, profile);
    }

    /**
     * Convert User + UserProfile into frontend-facing response DTO.
     */
    private UserProfileResponse mapToResponse(User user, UserProfile profile) {
        UserProfileResponse response = new UserProfileResponse();

        response.setFirstName(user.getFirstName());
        response.setLastName(user.getLastName());
        response.setPronouns(user.getPronouns());
        response.setEmail(user.getEmail());

        response.setLocation(profile.getLocation());
        response.setTargetRole(profile.getTargetRole());
        response.setYearsOfExperience(profile.getYearsOfExperience());
        response.setKeySkills(profile.getKeySkills());
        response.setPreferredTopK(profile.getPreferredTopK());

        return response;
    }
}
