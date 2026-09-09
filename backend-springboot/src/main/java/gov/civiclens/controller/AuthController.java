package gov.civiclens.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/v1/auth")
@CrossOrigin(origins = "*")
public class AuthController {

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> credentials) {
        String email = credentials.getOrDefault("email", "citizen@civiclens.gov");
        String role = email.contains("admin") ? "AUTHORITY_ADMIN" : "CITIZEN";
        String fullName = role.equals("AUTHORITY_ADMIN") ? "Chief Municipal Admin" : "Verified Citizen";

        Map<String, Object> user = new HashMap<>();
        user.put("id", UUID.randomUUID().toString());
        user.put("email", email);
        user.put("full_name", fullName);
        user.put("role", role);
        user.put("department", role.equals("AUTHORITY_ADMIN") ? "CENTRAL_COMMAND" : "CITIZEN");

        Map<String, Object> response = new HashMap<>();
        response.put("access_token", "jwt-mock-token-springboot-" + System.currentTimeMillis());
        response.put("token_type", "bearer");
        response.put("user", user);

        return ResponseEntity.ok(response);
    }

    @GetMapping("/me")
    public ResponseEntity<?> getCurrentUser(@RequestHeader(value = "Authorization", required = false) String token) {
        Map<String, Object> user = new HashMap<>();
        user.put("id", "usr-springboot-current");
        user.put("email", "citizen@civiclens.gov");
        user.put("full_name", "Verified Citizen");
        user.put("role", "CITIZEN");
        return ResponseEntity.ok(user);
    }
}
