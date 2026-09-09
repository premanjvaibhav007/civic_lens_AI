package gov.civiclens.ai.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Psychology
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import gov.civiclens.ai.R
import gov.civiclens.ai.ui.theme.CivicGreenPrimary
import gov.civiclens.ai.ui.theme.NavyDark

data class OnboardingStep(
    val titleRes: Int,
    val descRes: Int,
    val icon: ImageVector
)

@Composable
fun OnboardingScreen(
    onFinish: () -> Unit
) {
    val steps = listOf(
        OnboardingStep(R.string.onboarding_title_1, R.string.onboarding_desc_1, Icons.Default.CameraAlt),
        OnboardingStep(R.string.onboarding_title_2, R.string.onboarding_desc_2, Icons.Default.Psychology),
        OnboardingStep(R.string.onboarding_title_3, R.string.onboarding_desc_3, Icons.Default.CheckCircle)
    )

    var currentStep by remember { mutableStateOf(0) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(NavyDark)
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        // Top Step Indicator
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 24.dp),
            horizontalArrangement = Arrangement.Center
        ) {
            steps.forEachIndexed { index, _ ->
                Box(
                    modifier = Modifier
                        .padding(horizontal = 4.dp)
                        .height(4.dp)
                        .width(if (index == currentStep) 28.dp else 12.dp)
                        .background(
                            if (index == currentStep) CivicGreenPrimary else androidx.compose.ui.graphics.Color.DarkGray,
                            shape = RoundedCornerShape(2.dp)
                        )
                )
            }
        }

        // Center Content
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(horizontal = 16.dp)
        ) {
            Surface(
                shape = MaterialTheme.shapes.extraLarge,
                color = CivicGreenPrimary.copy(alpha = 0.15f),
                modifier = Modifier.size(110.dp)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        imageVector = steps[currentStep].icon,
                        contentDescription = null,
                        tint = CivicGreenPrimary,
                        modifier = Modifier.size(56.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(32.dp))

            Text(
                text = stringResource(steps[currentStep].titleRes),
                color = androidx.compose.ui.graphics.Color.White,
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = stringResource(steps[currentStep].descRes),
                color = androidx.compose.ui.graphics.Color.LightGray,
                fontSize = 14.sp,
                textAlign = TextAlign.Center,
                lineHeight = 20.sp
            )
        }

        // Bottom Action Button
        Button(
            onClick = {
                if (currentStep < steps.size - 1) {
                    currentStep++
                } else {
                    onFinish()
                }
            },
            colors = ButtonDefaults.buttonColors(containerColor = CivicGreenPrimary),
            shape = RoundedCornerShape(16.dp),
            modifier = Modifier
                .fillMaxWidth()
                .height(54.dp)
        ) {
            Text(
                text = if (currentStep == steps.size - 1) stringResource(R.string.btn_get_started) else "Next",
                color = NavyDark,
                fontWeight = FontWeight.Bold,
                fontSize = 16.sp
            )
        }
    }
}
