package com.example.bookwiseapp

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.bookwiseapp.ui.navigation.AppNav
import com.example.bookwiseapp.ui.theme.BookwiseAppTheme
import com.example.bookwiseapp.viewmodel.AuthViewModel

class MainActivity : ComponentActivity() {

    private val pendingDeepLink = mutableStateOf<Uri?>(null)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        pendingDeepLink.value = intent?.data
        enableEdgeToEdge()
        setContent {
            BookwiseAppTheme {
                val authVm: AuthViewModel = viewModel()
                var authReady by remember { mutableStateOf(false) }
                var startLoggedIn by remember { mutableStateOf(false) }

                LaunchedEffect(Unit) {
                    startLoggedIn = authVm.tryRestoreSession()
                    authReady = true
                }

                if (!authReady) {
                    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator()
                    }
                } else {
                    AppNav(
                        startLoggedIn = startLoggedIn,
                        deepLinkUri = pendingDeepLink
                    )
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        pendingDeepLink.value = intent.data
    }
}
