package gov.civiclens.ai.ui.screens

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import gov.civiclens.ai.R
import gov.civiclens.ai.ui.theme.*
import gov.civiclens.ai.ui.viewmodel.ComplaintViewModel
import java.io.File
import java.io.FileOutputStream

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReportIssueScreen(
    viewModel: ComplaintViewModel,
    onNavigateBack: () -> Unit,
    onSubmitSuccess: () -> Unit
) {
    val context = LocalContext.current
    var currentStep by remember { mutableStateOf(1) }

    var selectedImageUri by remember { mutableStateOf<Uri?>(null) }
    var title by remember { mutableStateOf(viewModel.draftTitle.ifEmpty { "Massive pothole on road" }) }
    var description by remember { mutableStateOf(viewModel.draftDescription.ifEmpty { "Deep crater on main road near bus stand. High risk of accidents." }) }
    var address by remember { mutableStateOf(viewModel.draftAddress) }
    var isSubmitting by remember { mutableStateOf(false) }

    // Photo Picker Launcher
    val photoPickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        if (uri != null) {
            selectedImageUri = uri
            // Cache file locally
            try {
                val inputStream = context.contentResolver.openInputStream(uri)
                val tempFile = File(context.cacheDir, "picked_complaint_${System.currentTimeMillis()}.jpg")
                val outputStream = FileOutputStream(tempFile)
                inputStream?.copyTo(outputStream)
                viewModel.draftImageFile = tempFile
                currentStep = 2
            } catch (e: Exception) {
                // Handle file error
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.nav_report), fontWeight = FontWeight.Bold) },
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
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(SlateBackground)
                .padding(paddingValues)
                .padding(16.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            // Stepper Progress Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                for (step in 1..4) {
                    val isDone = step < currentStep
                    val isCurrent = step == currentStep
                    Surface(
                        shape = RoundedCornerShape(10.dp),
                        color = if (isCurrent) CivicGreenPrimary else if (isDone) CivicGreenContainer else Color.LightGray.copy(alpha = 0.5f),
                        modifier = Modifier.size(36.dp)
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            if (isDone) {
                                Icon(Icons.Default.Check, contentDescription = null, tint = CivicGreenOnContainer, modifier = Modifier.size(18.dp))
                            } else {
                                Text(
                                    text = step.toString(),
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 14.sp,
                                    color = if (isCurrent) NavyDark else Color.DarkGray
                                )
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Step Content
            when (currentStep) {
                1 -> {
                    // STEP 1: Photo
                    Card(
                        shape = RoundedCornerShape(20.dp),
                        colors = CardDefaults.cardColors(containerColor = Color.White),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(20.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(stringResource(R.string.step_photo), fontSize = 18.sp, fontWeight = FontWeight.Bold, color = SlateTextPrimary)
                            Text("Provide clear visual evidence of the infrastructure issue.", fontSize = 12.sp, color = SlateTextSecondary, modifier = Modifier.padding(top = 4.dp, bottom = 24.dp))

                            Surface(
                                shape = RoundedCornerShape(16.dp),
                                color = SlateBackground,
                                border = androidx.compose.foundation.BorderStroke(2.dp, SlateBorder),
                                modifier = Modifier.fillMaxWidth().height(180.dp)
                            ) {
                                Box(contentAlignment = Alignment.Center) {
                                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                        Icon(Icons.Default.AddAPhoto, contentDescription = null, tint = CivicGreenPrimary, modifier = Modifier.size(48.dp))
                                        Spacer(modifier = Modifier.height(8.dp))
                                        Text("Select Image for AI Inspection", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = SlateTextPrimary)
                                    }
                                }
                            }

                            Spacer(modifier = Modifier.height(20.dp))

                            Button(
                                onClick = { photoPickerLauncher.launch("image/*") },
                                colors = ButtonDefaults.buttonColors(containerColor = CivicGreenPrimary),
                                shape = RoundedCornerShape(12.dp),
                                modifier = Modifier.fillMaxWidth().height(48.dp)
                            ) {
                                Icon(Icons.Default.PhotoLibrary, contentDescription = null, tint = NavyDark)
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(stringResource(R.string.gallery_pick), color = NavyDark, fontWeight = FontWeight.Bold)
                            }

                            Spacer(modifier = Modifier.height(8.dp))

                            OutlinedButton(
                                onClick = { currentStep = 2 },
                                shape = RoundedCornerShape(12.dp),
                                modifier = Modifier.fillMaxWidth().height(48.dp)
                            ) {
                                Text("Skip Photo (Text Report)", color = SlateTextPrimary)
                            }
                        }
                    }
                }

                2 -> {
                    // STEP 2: Location
                    Card(
                        shape = RoundedCornerShape(20.dp),
                        colors = CardDefaults.cardColors(containerColor = Color.White),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(20.dp)) {
                            Text(stringResource(R.string.step_location), fontSize = 18.sp, fontWeight = FontWeight.Bold, color = SlateTextPrimary)
                            Text("Confirm incident GPS coordinates for municipal dispatch.", fontSize = 12.sp, color = SlateTextSecondary, modifier = Modifier.padding(top = 4.dp, bottom = 16.dp))

                            OutlinedTextField(
                                value = address,
                                onValueChange = { address = it },
                                label = { Text("Street Address / Landmark") },
                                leadingIcon = { Icon(Icons.Default.LocationOn, contentDescription = null, tint = CivicGreenPrimary) },
                                modifier = Modifier.fillMaxWidth()
                            )

                            Spacer(modifier = Modifier.height(12.dp))

                            Surface(
                                shape = RoundedCornerShape(12.dp),
                                color = SlateBackground,
                                modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp)
                            ) {
                                Row(modifier = Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                                    Icon(Icons.Default.GpsFixed, contentDescription = null, tint = CivicGreenPrimary, modifier = Modifier.size(20.dp))
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Column {
                                        Text("Captured GPS Location", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = SlateTextPrimary)
                                        Text("Lat: 28.6328 • Lng: 77.2197 (Accuracy: 4.2m)", fontSize = 10.sp, color = SlateTextSecondary)
                                    }
                                }
                            }

                            Spacer(modifier = Modifier.height(16.dp))

                            Button(
                                onClick = {
                                    viewModel.draftAddress = address
                                    currentStep = 3
                                },
                                colors = ButtonDefaults.buttonColors(containerColor = CivicGreenPrimary),
                                shape = RoundedCornerShape(12.dp),
                                modifier = Modifier.fillMaxWidth().height(48.dp)
                            ) {
                                Text("Confirm Location", color = NavyDark, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }

                3 -> {
                    // STEP 3: Issue Details
                    Card(
                        shape = RoundedCornerShape(20.dp),
                        colors = CardDefaults.cardColors(containerColor = Color.White),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(20.dp)) {
                            Text(stringResource(R.string.step_details), fontSize = 18.sp, fontWeight = FontWeight.Bold, color = SlateTextPrimary)
                            Text("Provide a descriptive title and context.", fontSize = 12.sp, color = SlateTextSecondary, modifier = Modifier.padding(top = 4.dp, bottom = 16.dp))

                            OutlinedTextField(
                                value = title,
                                onValueChange = { title = it },
                                label = { Text("Issue Title") },
                                placeholder = { Text(stringResource(R.string.title_hint)) },
                                modifier = Modifier.fillMaxWidth()
                            )

                            Spacer(modifier = Modifier.height(12.dp))

                            OutlinedTextField(
                                value = description,
                                onValueChange = { description = it },
                                label = { Text("Detailed Description") },
                                placeholder = { Text(stringResource(R.string.desc_hint)) },
                                minLines = 3,
                                modifier = Modifier.fillMaxWidth()
                            )

                            Spacer(modifier = Modifier.height(16.dp))

                            Button(
                                onClick = {
                                    viewModel.draftTitle = title
                                    viewModel.draftDescription = description
                                    currentStep = 4
                                },
                                colors = ButtonDefaults.buttonColors(containerColor = CivicGreenPrimary),
                                shape = RoundedCornerShape(12.dp),
                                modifier = Modifier.fillMaxWidth().height(48.dp)
                            ) {
                                Text("Review & Preview AI", color = NavyDark, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }

                4 -> {
                    // STEP 4: AI Review & Submit
                    Card(
                        shape = RoundedCornerShape(20.dp),
                        colors = CardDefaults.cardColors(containerColor = Color.White),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(20.dp)) {
                            Text(stringResource(R.string.step_review), fontSize = 18.sp, fontWeight = FontWeight.Bold, color = SlateTextPrimary)
                            Text("Verify all information before automated routing.", fontSize = 12.sp, color = SlateTextSecondary, modifier = Modifier.padding(top = 4.dp, bottom = 16.dp))

                            Surface(
                                shape = RoundedCornerShape(14.dp),
                                color = NavyDark,
                                modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp)
                            ) {
                                Column(modifier = Modifier.padding(16.dp)) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Icon(Icons.Default.AutoAwesome, contentDescription = null, tint = CivicGreenPrimary, modifier = Modifier.size(18.dp))
                                        Spacer(modifier = Modifier.width(6.dp))
                                        Text("AI Triage Dispatch", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                                    }
                                    Spacer(modifier = Modifier.height(8.dp))
                                    Text("• Automated multimodal image & NLP classification", color = Color.LightGray, fontSize = 11.sp)
                                    Text("• Spatial-temporal duplicate detection (200m radius)", color = Color.LightGray, fontSize = 11.sp)
                                    Text("• Dynamic jurisdiction & priority assignment (P1-P4)", color = Color.LightGray, fontSize = 11.sp)
                                }
                            }

                            Text("Title: $title", fontWeight = FontWeight.Bold, fontSize = 14.sp, color = SlateTextPrimary)
                            Text("Location: $address", fontSize = 12.sp, color = SlateTextSecondary, modifier = Modifier.padding(top = 4.dp))
                            Text("Description: $description", fontSize = 12.sp, color = SlateTextSecondary, modifier = Modifier.padding(top = 4.dp, bottom = 20.dp))

                            Button(
                                onClick = {
                                    isSubmitting = true
                                    viewModel.submitCurrentDraft { success ->
                                        isSubmitting = false
                                        if (success) onSubmitSuccess()
                                    }
                                },
                                enabled = !isSubmitting,
                                colors = ButtonDefaults.buttonColors(containerColor = CivicGreenPrimary),
                                shape = RoundedCornerShape(12.dp),
                                modifier = Modifier.fillMaxWidth().height(52.dp)
                            ) {
                                if (isSubmitting) {
                                    CircularProgressIndicator(color = NavyDark, modifier = Modifier.size(24.dp))
                                } else {
                                    Icon(Icons.Default.Send, contentDescription = null, tint = NavyDark)
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text(stringResource(R.string.btn_submit_complaint), color = NavyDark, fontWeight = FontWeight.Bold, fontSize = 15.sp)
                                }
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}
