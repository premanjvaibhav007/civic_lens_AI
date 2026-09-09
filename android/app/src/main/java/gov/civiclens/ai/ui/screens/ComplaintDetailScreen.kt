package gov.civiclens.ai.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import gov.civiclens.ai.R
import gov.civiclens.ai.ui.theme.*
import gov.civiclens.ai.ui.viewmodel.ComplaintViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ComplaintDetailScreen(
    complaintId: String,
    viewModel: ComplaintViewModel,
    onNavigateBack: () -> Unit
) {
    val complaintDetail by viewModel.selectedComplaint.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()

    var showVerifyDialog by remember { mutableStateOf(false) }
    var verifyIsResolved by remember { mutableStateOf(true) }
    var verifyRating by remember { mutableStateOf(5) }
    var verifyFeedback by remember { mutableStateOf("") }

    LaunchedEffect(complaintId) {
        viewModel.loadComplaintDetail(complaintId)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(complaintDetail?.complaintNumber ?: "Complaint Details", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = NavyDark,
                    titleContentColor = Color.White,
                    navigationIconContentColor = Color.White
                )
            )
        }
    ) { paddingValues ->
        if (isLoading || complaintDetail == null) {
            Box(modifier = Modifier.fillMaxSize().padding(paddingValues), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = CivicGreenPrimary)
            }
        } else {
            val c = complaintDetail!!
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .background(SlateBackground)
                    .padding(paddingValues)
                    .padding(16.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Header Status Card
                Card(
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.cardColors(containerColor = Color.White),
                    elevation = CardDefaults.cardElevation(2.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(c.complaintNumber, fontWeight = FontWeight.Bold, color = CivicGreenPrimary, fontSize = 13.sp)
                            StatusChip(status = c.status)
                        }

                        Spacer(modifier = Modifier.height(10.dp))

                        Text(c.title, fontWeight = FontWeight.Bold, fontSize = 16.sp, color = SlateTextPrimary)
                        Text(c.description ?: "No description provided.", fontSize = 13.sp, color = SlateTextSecondary, modifier = Modifier.padding(top = 6.dp))

                        if (!c.address.isNullOrEmpty()) {
                            Spacer(modifier = Modifier.height(10.dp))
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.LocationOn, contentDescription = null, tint = CivicGreenPrimary, modifier = Modifier.size(14.dp))
                                Spacer(modifier = Modifier.width(4.dp))
                                Text(c.address, fontSize = 12.sp, color = SlateTextSecondary)
                            }
                        }
                    }
                }

                // AI Triage Report Card
                if (c.aiAnalysis != null) {
                    Card(
                        shape = RoundedCornerShape(20.dp),
                        colors = CardDefaults.cardColors(containerColor = NavyDark),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(20.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.AutoAwesome, contentDescription = null, tint = CivicGreenPrimary, modifier = Modifier.size(20.dp))
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(stringResource(R.string.ai_analysis_title), color = Color.White, fontWeight = FontWeight.Bold, fontSize = 15.sp)
                            }

                            Spacer(modifier = Modifier.height(12.dp))

                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Column {
                                    Text(stringResource(R.string.ai_detected_issue), color = Color.LightGray, fontSize = 11.sp)
                                    Text(c.aiAnalysis.detectedCategory, color = CivicGreenPrimary, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                                }
                                Column {
                                    Text(stringResource(R.string.ai_confidence), color = Color.LightGray, fontSize = 11.sp)
                                    Text("${(c.aiAnalysis.confidence * 100).toInt()}%", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                                }
                                Column {
                                    Text(stringResource(R.string.ai_priority), color = Color.LightGray, fontSize = 11.sp)
                                    Text(c.aiAnalysis.predictedPriority, color = PriorityCritical, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                                }
                            }

                            if (!c.aiAnalysis.explanationText.isNullOrEmpty()) {
                                Spacer(modifier = Modifier.height(12.dp))
                                Surface(
                                    color = Color.White.copy(alpha = 0.08f),
                                    shape = RoundedCornerShape(10.dp),
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text(
                                        text = c.aiAnalysis.explanationText,
                                        color = Color.LightGray,
                                        fontSize = 11.sp,
                                        modifier = Modifier.padding(10.dp)
                                    )
                                }
                            }
                        }
                    }
                }

                // Citizen Verification Card (If status is RESOLUTION_SUBMITTED)
                if (c.status == "RESOLUTION_SUBMITTED" || c.status == "CITIZEN_VERIFICATION") {
                    Card(
                        shape = RoundedCornerShape(20.dp),
                        colors = CardDefaults.cardColors(containerColor = CivicGreenContainer),
                        border = androidx.compose.foundation.BorderStroke(1.5.dp, CivicGreenPrimary),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(20.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.Verified, contentDescription = null, tint = CivicGreenPrimary, modifier = Modifier.size(22.dp))
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(stringResource(R.string.verification_prompt), color = CivicGreenOnContainer, fontWeight = FontWeight.Bold, fontSize = 15.sp)
                            }

                            if (c.resolutionEvidence != null) {
                                Spacer(modifier = Modifier.height(8.dp))
                                Text("Officer Remarks: ${c.resolutionEvidence.completionNote}", fontSize = 12.sp, color = CivicGreenOnContainer)

                                if (c.resolutionEvidence.aiResolutionConfidence != null) {
                                    Spacer(modifier = Modifier.height(6.dp))
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        val isVerified = c.resolutionEvidence.aiLikelyResolved == true
                                        val iconTint = if (isVerified) CivicGreenPrimary else PriorityMedium
                                        Icon(Icons.Default.AutoAwesome, contentDescription = null, tint = iconTint, modifier = Modifier.size(16.dp))
                                        Spacer(modifier = Modifier.width(6.dp))
                                        val confPct = (c.resolutionEvidence.aiResolutionConfidence * 100).toInt()
                                        val statusLabel = if (isVerified) "AI Verified Resolved (${confPct}% confidence)" else "AI Quality Flagged (${confPct}% confidence)"
                                        Text(
                                            text = statusLabel,
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.SemiBold,
                                            color = CivicGreenOnContainer
                                        )
                                    }
                                }
                            }

                            Spacer(modifier = Modifier.height(16.dp))

                            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                Button(
                                    onClick = {
                                        verifyIsResolved = true
                                        showVerifyDialog = true
                                    },
                                    colors = ButtonDefaults.buttonColors(containerColor = CivicGreenPrimary),
                                    shape = RoundedCornerShape(12.dp),
                                    modifier = Modifier.weight(1f)
                                ) {
                                    Text(stringResource(R.string.btn_resolved_yes), color = NavyDark, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                                }

                                OutlinedButton(
                                    onClick = {
                                        verifyIsResolved = false
                                        showVerifyDialog = true
                                    },
                                    shape = RoundedCornerShape(12.dp),
                                    colors = ButtonDefaults.outlinedButtonColors(contentColor = PriorityCritical),
                                    modifier = Modifier.weight(1f)
                                ) {
                                    Text(stringResource(R.string.btn_resolved_no), fontWeight = FontWeight.Bold, fontSize = 12.sp)
                                }
                            }
                        }
                    }
                }

                // Timeline Section
                Card(
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.cardColors(containerColor = Color.White),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        Text("Resolution Timeline", fontWeight = FontWeight.Bold, fontSize = 15.sp, color = SlateTextPrimary)
                        Spacer(modifier = Modifier.height(12.dp))

                        c.timeline.forEach { item ->
                            Row(modifier = Modifier.padding(vertical = 6.dp), verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.CheckCircle, contentDescription = null, tint = CivicGreenPrimary, modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(8.dp))
                                Column {
                                    Text(item.newStatus.replace("_", " "), fontWeight = FontWeight.SemiBold, fontSize = 12.sp, color = SlateTextPrimary)
                                    if (!item.reason.isNullOrEmpty()) {
                                        Text(item.reason, fontSize = 11.sp, color = SlateTextSecondary)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Verification Dialog Modal
    if (showVerifyDialog) {
        AlertDialog(
            onDismissRequest = { showVerifyDialog = false },
            title = {
                Text(
                    text = if (verifyIsResolved) "Confirm Resolution" else "Reopen Complaint",
                    fontWeight = FontWeight.Bold
                )
            },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    if (verifyIsResolved) {
                        Text("Rate resolution quality:", fontSize = 12.sp)
                        Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                            for (star in 1..5) {
                                IconButton(onClick = { verifyRating = star }, modifier = Modifier.size(32.dp)) {
                                    Icon(
                                        Icons.Default.Star,
                                        contentDescription = null,
                                        tint = if (star <= verifyRating) PriorityMedium else Color.LightGray
                                    )
                                }
                            }
                        }
                    }
                    OutlinedTextField(
                        value = verifyFeedback,
                        onValueChange = { verifyFeedback = it },
                        label = { Text(if (verifyIsResolved) "Feedback (optional)" else "Reopen Reason") },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        viewModel.verifyResolution(
                            complaintId = complaintId,
                            isResolved = verifyIsResolved,
                            rating = if (verifyIsResolved) verifyRating else null,
                            feedback = verifyFeedback,
                            reopenReason = if (!verifyIsResolved) verifyFeedback else null
                        ) {
                            showVerifyDialog = false
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = CivicGreenPrimary)
                ) {
                    Text("Submit", color = NavyDark, fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                TextButton(onClick = { showVerifyDialog = false }) {
                    Text("Cancel")
                }
            }
        )
    }
}
