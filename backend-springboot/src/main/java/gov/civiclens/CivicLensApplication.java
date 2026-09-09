package gov.civiclens;

import gov.civiclens.model.Complaint;
import gov.civiclens.repository.ComplaintRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

import java.time.LocalDateTime;

@SpringBootApplication
public class CivicLensApplication {

    public static void main(String[] args) {
        SpringApplication.run(CivicLensApplication.class, args);
        System.out.println("==========================================================");
        System.out.println("🚀 CivicLens AI Spring Boot Service Started on Port 8080");
        System.out.println("👉 REST API: http://localhost:8080/api/v1/complaints");
        System.out.println("👉 Health Check: http://localhost:8080/health");
        System.out.println("👉 H2 Console: http://localhost:8080/h2-console");
        System.out.println("==========================================================");
    }

    @Bean
    CommandLineRunner seedDemoData(ComplaintRepository repository) {
        return args -> {
            if (repository.count() == 0) {
                Complaint c1 = new Complaint();
                c1.setTitle("Massive Hazardous Pothole Near Metro Gate 3");
                c1.setDescription("Deep tire-bursting pothole causing traffic jam and bicycle accidents.");
                c1.setCategory("POTHOLE");
                c1.setSeverity("HIGH");
                c1.setPriority("P1");
                c1.setStatus("IN_PROGRESS");
                c1.setDepartment("ROADS_HIGHWAYS");
                c1.setLatitude(28.6139);
                c1.setLongitude(77.2090);
                c1.setCitizenEmail("citizen@civiclens.gov");
                c1.setOfficerName("Eng. Rajesh Kumar");
                c1.setCreatedAt(LocalDateTime.now().minusHours(4));
                c1.setUpdatedAt(LocalDateTime.now().minusMinutes(30));
                repository.save(c1);

                Complaint c2 = new Complaint();
                c2.setTitle("High Pressure Clean Water Main Burst");
                c2.setDescription("Piped water main damaged, flooding the primary school road.");
                c2.setCategory("WATER_LEAKAGE");
                c2.setSeverity("CRITICAL");
                c2.setPriority("P1");
                c2.setStatus("PENDING");
                c2.setDepartment("WATER_SEWERAGE");
                c2.setLatitude(28.6152);
                c2.setLongitude(77.2105);
                c2.setCitizenEmail("citizen@civiclens.gov");
                c2.setCreatedAt(LocalDateTime.now().minusHours(2));
                c2.setUpdatedAt(LocalDateTime.now().minusHours(2));
                repository.save(c2);

                Complaint c3 = new Complaint();
                c3.setTitle("Broken Streetlight In Dark Residential Alley");
                c3.setDescription("Pedestrian safety risk due to complete blackout at night.");
                c3.setCategory("STREETLIGHT");
                c3.setSeverity("MEDIUM");
                c3.setPriority("P2");
                c3.setStatus("RESOLVED");
                c3.setDepartment("ELECTRICAL");
                c3.setLatitude(28.6120);
                c3.setLongitude(77.2080);
                c3.setCitizenEmail("citizen@civiclens.gov");
                c3.setOfficerName("Officer Amit Sharma");
                c3.setCreatedAt(LocalDateTime.now().minusDays(1));
                c3.setUpdatedAt(LocalDateTime.now().minusHours(5));
                repository.save(c3);
            }
        };
    }
}
