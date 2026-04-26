package com.example.jobplatform.controller;

import com.example.jobplatform.dto.AiUploadResponse;
import com.example.jobplatform.service.AiRecommendationService;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

/**
 * REST controller for job recommendation requests.
 *
 * This endpoint accepts a resume file from the frontend,
 * forwards it to the FastAPI AI service, and returns
 * the AI-generated job recommendations.
 */
@RestController
@CrossOrigin(origins = "http://localhost:5173")
@RequestMapping("/api/recommendations")
public class JobRecommendationController {

    private final AiRecommendationService aiRecommendationService;

    public JobRecommendationController(AiRecommendationService aiRecommendationService) {
        this.aiRecommendationService = aiRecommendationService;
    }

    @PostMapping(value = "/upload-resume", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public AiUploadResponse uploadResume(
            @RequestPart("file") MultipartFile file,
            @RequestParam(defaultValue = "5") @Min(1) int topK
    ) {
        return aiRecommendationService.uploadResumeAndGetRecommendations(file, topK);
    }

    @GetMapping("/health")
    public String health() {
        return "Spring Boot recommendation backend is running";
    }
}
