package com.example.bookwiseapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.example.bookwiseapp.data.api.ApiClient
import com.example.bookwiseapp.ui.navigation.AppNav
import com.example.bookwiseapp.ui.theme.BookwiseAppTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        // ApiClient.token 已在 Application.onCreate 中由 TokenStore 恢复
        val startLoggedIn = ApiClient.token != null
        setContent {
            BookwiseAppTheme {
                AppNav(startLoggedIn = startLoggedIn)
            }
        }
    }
}
