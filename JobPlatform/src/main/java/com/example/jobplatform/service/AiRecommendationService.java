package com.example.jobplatform.service;

import com.example.jobplatform.dto.AiUploadResponse;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClient;

/**
 * Service responsible for forwarding uploaded resume files
 * from Spring Boot to the FastAPI AI service.
 */
@Service
public class AiRecommendationService {

    private final WebClient aiWebClient;

    public AiRecommendationService(WebClient aiWebClient) {
        this.aiWebClient = aiWebClient;
    }

    public AiUploadResponse uploadResumeAndGetRecommendations(MultipartFile file, int topK) {
        try {
            MultipartBodyBuilder builder = new MultipartBodyBuilder();

            // Wrap the uploaded file bytes in a ByteArrayResource
            // and preserve the original filename.
            ByteArrayResource fileResource = new ByteArrayResource(file.getBytes()) {
                @Override
                public String getFilename() {
                    return file.getOriginalFilename();
                }
            };

            // Add multipart fields expected by FastAPI:
            // - file
            // - top_k
            builder.part("file", fileResource)
                    .contentType(MediaType.APPLICATION_OCTET_STREAM);

            builder.part("top_k", String.valueOf(topK));

            return aiWebClient.post()
                    .uri("/match/upload-resume")
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .bodyValue(builder.build())
                    .retrieve()
                    .bodyToMono(AiUploadResponse.class)
                    .block();

        } catch (Exception e) {
            throw new RuntimeException("Failed to send resume to AI service: " + e.getMessage(), e);
        }
    }
}
