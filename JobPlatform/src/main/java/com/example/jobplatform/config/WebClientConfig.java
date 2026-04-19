package com.example.jobplatform.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

/**
 * Configuration class for creating a WebClient bean
 * that points to the FastAPI AI service.
 */
@Configuration
public class WebClientConfig {

    @Bean
    public WebClient aiWebClient(@Value("${ai.service.base-url}") String baseUrl) {
        return WebClient.builder()
                .baseUrl(baseUrl)
                .build();
    }
}
