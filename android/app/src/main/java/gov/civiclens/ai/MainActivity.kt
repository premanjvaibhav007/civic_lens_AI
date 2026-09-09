package gov.civiclens.ai

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import gov.civiclens.ai.ui.screens.*
import gov.civiclens.ai.ui.theme.CivicLensAITheme
import gov.civiclens.ai.ui.viewmodel.AuthViewModel
import gov.civiclens.ai.ui.viewmodel.ComplaintViewModel

class MainActivity : ComponentActivity() {
    private val authViewModel: AuthViewModel by viewModels()
    private val complaintViewModel: ComplaintViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            CivicLensAITheme {
                CivicLensAppNavHost(
                    authViewModel = authViewModel,
                    complaintViewModel = complaintViewModel
                )
            }
        }
    }
}

@Composable
fun CivicLensAppNavHost(
    authViewModel: AuthViewModel,
    complaintViewModel: ComplaintViewModel
) {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = "splash"
    ) {
        composable("splash") {
            SplashScreen(
                onTimeout = {
                    navController.navigate("onboarding") {
                        popUpTo("splash") { inclusive = true }
                    }
                }
            )
        }

        composable("onboarding") {
            OnboardingScreen(
                onFinish = {
                    navController.navigate("auth") {
                        popUpTo("onboarding") { inclusive = true }
                    }
                }
            )
        }

        composable("auth") {
            AuthScreen(
                viewModel = authViewModel,
                onAuthSuccess = {
                    navController.navigate("home") {
                        popUpTo("auth") { inclusive = true }
                    }
                }
            )
        }

        composable("home") {
            HomeScreen(
                viewModel = complaintViewModel,
                onNavigateToReport = { navController.navigate("report") },
                onNavigateToDetail = { id -> navController.navigate("detail/$id") },
                onNavigateToMap = { navController.navigate("map") }
            )
        }

        composable("report") {
            ReportIssueScreen(
                viewModel = complaintViewModel,
                onNavigateBack = { navController.popBackStack() },
                onSubmitSuccess = {
                    navController.navigate("home") {
                        popUpTo("report") { inclusive = true }
                    }
                }
            )
        }

        composable(
            route = "detail/{id}",
            arguments = listOf(navArgument("id") { type = NavType.StringType })
        ) { backStackEntry ->
            val id = backStackEntry.arguments?.getString("id") ?: ""
            ComplaintDetailScreen(
                complaintId = id,
                viewModel = complaintViewModel,
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable("map") {
            NearbyMapScreen(
                viewModel = complaintViewModel,
                onNavigateBack = { navController.popBackStack() },
                onSelectComplaint = { id -> navController.navigate("detail/$id") }
            )
        }
    }
}
