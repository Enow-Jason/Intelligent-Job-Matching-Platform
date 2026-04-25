package com.example.jobplatform.controller;

import com.example.jobplatform.dto.ChangePasswordRequest;
import com.example.jobplatform.dto.SignInRequest;
import com.example.jobplatform.dto.SignUpRequest;
import com.example.jobplatform.dto.UserProfileRequest;
import com.example.jobplatform.dto.UserProfileResponse;
import com.example.jobplatform.service.UserProfileService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * Controller for user account creation, sign-in,
 * password changes, and profile persistence.
 */
@RestController
@RequestMapping("/api/users")
@CrossOrigin(origins = "http://localhost:5173")
public class UserProfileController {

    private final UserProfileService userProfileService;

    public UserProfileController(UserProfileService userProfileService) {
        this.userProfileService = userProfileService;
    }

    /**
     * Create a new account.
     */
    @PostMapping("/signup")
    public UserProfileResponse signUp(@Valid @RequestBody SignUpRequest request) {
        return userProfileService.createUser(request);
    }

    /**
     * Real password-based sign-in.
     */
    @PostMapping("/signin")
    public UserProfileResponse signIn(@Valid @RequestBody SignInRequest request) {
        return userProfileService.authenticateUser(request);
    }

    /**
     * Change password for a local account.
     */
    @PostMapping("/change-password")
    public Map<String, String> changePassword(@Valid @RequestBody ChangePasswordRequest request) {
        userProfileService.changePassword(request);
        return Map.of("message", "Password updated successfully.");
    }

    /**
     * Save user profile fields.
     */
    @PostMapping("/profile")
    public UserProfileResponse saveProfile(@RequestBody UserProfileRequest request) {
        return userProfileService.saveProfile(request);
    }

    /**
     * Load user profile by email.
     */
    @GetMapping("/profile")
    public UserProfileResponse getProfile(@RequestParam String email) {
        return userProfileService.getProfileByEmail(email);
    }
}
