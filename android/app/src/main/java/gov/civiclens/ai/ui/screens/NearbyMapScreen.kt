package gov.civiclens.ai.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
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
fun NearbyMapScreen(
    viewModel: ComplaintViewModel,
    onNavigateBack: () -> Unit,
    onSelectComplaint: (String) -> Unit
) {
    val nearbyComplaints by viewModel.nearbyComplaints.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.nav_map), fontWeight = FontWeight.Bold) },
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
        ) {
            // Simulated Map Canvas Header
            Surface(
                color = NavyDark,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(240.dp)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(Icons.Default.Map, contentDescription = null, tint = CivicGreenPrimary, modifier = Modifier.size(48.dp))
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("Interactive Civic Issue Map", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                        Text("Showing ${nearbyComplaints.size} verified issues near Connaught Place", color = Color.LightGray, fontSize = 12.sp)
                    }
                }
            }

            // Nearby Issues List
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                item {
                    Text(
                        text = "Nearby Public Infrastructure Issues",
                        fontWeight = FontWeight.Bold,
                        fontSize = 15.sp,
                        color = SlateTextPrimary
                    )
                }

                items(nearbyComplaints) { item ->
                    ComplaintCard(complaint = item, onClick = { onSelectComplaint(item.id) })
                }
            }
        }
    }
}
