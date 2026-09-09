package gov.civiclens.repository;

import gov.civiclens.model.Complaint;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ComplaintRepository extends JpaRepository<Complaint, Long> {
    List<Complaint> findByCitizenEmailOrderByCreatedAtDesc(String citizenEmail);
    List<Complaint> findByDepartment(String department);
    List<Complaint> findByStatus(String status);
    List<Complaint> findAllByOrderByCreatedAtDesc();
}
