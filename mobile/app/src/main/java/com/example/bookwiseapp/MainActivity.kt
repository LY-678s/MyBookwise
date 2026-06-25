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
import com.example.bookwiseapp.util.StripeDeepLink
import com.example.bookwiseapp.util.parsePaymentDeepLink
import com.example.bookwiseapp.viewmodel.AuthViewModel

/** 每次支付回跳使用新 nonce，确保 Compose 能重复处理同一 URI。 */
data class PaymentReturn(val uri: Uri, val nonce: Long)

class MainActivity : ComponentActivity() {

    private val paymentReturn = mutableStateOf<PaymentReturn?>(null)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        publishPaymentReturn(intent)
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
                        paymentReturn = paymentReturn
                    )
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        publishPaymentReturn(intent)
    }

    override fun onResume() {
        super.onResume()
        // 从 Stripe / 浏览器切回时，即使 URI 与上次相同也再次投递
        publishPaymentReturn(intent)
    }

    private fun publishPaymentReturn(intent: Intent?) {
        val uri = intent?.data ?: return
        if (uri.scheme != StripeDeepLink.SCHEME || uri.host != StripeDeepLink.HOST) return
        if (parsePaymentDeepLink(uri) == null && uri.getQueryParameter("session_id").isNullOrBlank()) return
        paymentReturn.value = PaymentReturn(uri, System.nanoTime())
        // 避免 onResume 重复处理同一支付回跳
        intent.data = null
        setIntent(intent)
    }
}
