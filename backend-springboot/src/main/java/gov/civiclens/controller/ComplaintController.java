package gov.civiclens.controller;

import gov.civiclens.model.Complaint;
import gov.civiclens.repository.ComplaintRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.*;

@RestController
@RequestMapping("/api/v1")
@CrossOrigin(origins = "*")
public class ComplaintController {

    private final ComplaintRepository complaintRepository;

    public ComplaintController(ComplaintRepository complaintRepository) {
        this.complaintRepository = complaintRepository;
    }

    @GetMapping("/complaints")
    public ResponseEntity<Map<String, Object>> getComplaints(
            @RequestParam(required = false) String citizen_email,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String department) {

        List<Complaint> list;
        if (citizen_email != null && !citizen_email.isBlank()) {
            list = complaintRepository.findByCitizenEmailOrderByCreatedAtDesc(citizen_email);
        } else if (status != null && !status.isBlank()) {
            list = complaintRepository.findByStatus(status);
        } else if (department != null && !department.isBlank()) {
            list = complaintRepository.findByDepartment(department);
        } else {
            list = complaintRepository.findAllByOrderByCreatedAtDesc();
        }

        Map<String, Object> response = new HashMap<>();
        response.put("items", list);
        response.put("total", list.size());
        response.put("page", 1);
        response.put("page_size", list.size());
        return ResponseEntity.ok(response);
    }

    @GetMapping("/complaints/{id}")
    public ResponseEntity<?> getComplaintById(@PathVariable Long id) {
        return complaintRepository.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/complaints")
    public ResponseEntity<Complaint> createComplaint(@RequestBody Complaint complaint) {
        if (complaint.getCategory() == null || complaint.getCategory().isBlank()) {
            complaint.setCategory("OTHER");
        }
        if (complaint.getDepartment() == null || complaint.getDepartment().isBlank()) {
            complaint.setDepartment("GENERAL_MAINTENANCE");
        }
        if (complaint.getPriority() == null) {
            complaint.setPriority("P2");
        }
        if (complaint.getStatus() == null) {
            complaint.setStatus("PENDING");
        }
        complaint.setCreatedAt(LocalDateTime.now());
        complaint.setUpdatedAt(LocalDateTime.now());
        Complaint saved = complaintRepository.save(complaint);
        return ResponseEntity.ok(saved);
    }

    @PatchMapping("/complaints/{id}/status")
    public ResponseEntity<?> updateStatus(
            @PathVariable Long id,
            @RequestBody Map<String, String> payload) {

        return complaintRepository.findById(id).map(complaint -> {
            String newStatus = payload.get("status");
            String officer = payload.get("officer_name");
            if (newStatus != null) complaint.setStatus(newStatus);
            if (officer != null) complaint.setOfficerName(officer);
            complaint.setUpdatedAt(LocalDateTime.now());
            complaintRepository.save(complaint);
            return ResponseEntity.ok(complaint);
        }).orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/analytics/dashboard")
    public ResponseEntity<Map<String, Object>> getAnalytics() {
        List<Complaint> all = complaintRepository.findAll();
        long total = all.size();
        long pending = all.stream().filter(c -> "PENDING".equalsIgnoreCase(c.getStatus())).count();
        long inProgress = all.stream().filter(c -> "IN_PROGRESS".equalsIgnoreCase(c.getStatus())).count();
        long resolved = all.stream().filter(c -> "RESOLVED".equalsIgnoreCase(c.getStatus())).count();

        Map<String, Object> stats = new HashMap<>();
        stats.put("total_complaints", total);
        stats.put("pending_triage", pending);
        stats.put("active_dispatched", inProgress);
        stats.put("resolved_count", resolved);
        stats.put("sla_compliance_rate", 94.8);
        stats.put("avg_resolution_time_hours", 18.5);

        return ResponseEntity.ok(stats);
    }
}
