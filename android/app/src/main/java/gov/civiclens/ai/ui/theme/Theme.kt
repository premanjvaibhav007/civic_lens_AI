package gov.civiclens.ai.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val LightColorScheme = lightColorScheme(
    primary = CivicGreenPrimary,
    onPrimary = androidx.compose.ui.graphics.Color.White,
    primaryContainer = CivicGreenContainer,
    onPrimaryContainer = CivicGreenOnContainer,
    secondary = NavyDark,
    onSecondary = androidx.compose.ui.graphics.Color.White,
    background = SlateBackground,
    surface = androidx.compose.ui.graphics.Color.White,
    onBackground = SlateTextPrimary,
    onSurface = SlateTextPrimary
)

private val DarkColorScheme = darkColorScheme(
    primary = CivicGreenPrimary,
    onPrimary = androidx.compose.ui.graphics.Color.White,
    primaryContainer = CivicGreenDark,
    onPrimaryContainer = CivicGreenContainer,
    secondary = CivicGreenContainer,
    background = NavyDark,
    surface = NavySurface,
    onBackground = androidx.compose.ui.graphics.Color.White,
    onSurface = androidx.compose.ui.graphics.Color.White
)

@Composable
fun CivicLensAITheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.secondary.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = false
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        content = content
    )
}
