package com.example.jobplatform.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

/**
 * Basic security configuration.
 *
 * For now:
 * - BCrypt for password hashing
 * - API access allowed without Spring Security login screens
 */
@Configuration
public class SecurityConfig {

    /**
     * Password encoder bean for hashing and verifying passwords.
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * Security filter chain.
     *
     * We permit all requests for now because authentication is handled
     * manually via signup/signin endpoints, not Spring Security sessions yet.
     */
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                // Disable CSRF for local API development
                .csrf(csrf -> csrf.disable())
                // Allow CORS defaults
                .cors(Customizer.withDefaults())
                // Allow all requests for now
                .authorizeHttpRequests(auth -> auth
                        .anyRequest().permitAll()
                );

        return http.build();
    }
}
