package com.example.bookwiseapp.util

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.browser.customtabs.CustomTabsIntent

/** 使用 Chrome Custom Tabs 打开 Stripe，支付完成后更容易回到 App。 */
object StripeCheckout {
    fun open(context: Context, url: String) {
        val uri = Uri.parse(url)
        try {
            CustomTabsIntent.Builder()
                .setShowTitle(true)
                .build()
                .launchUrl(context, uri)
        } catch (_: Exception) {
            context.startActivity(Intent(Intent.ACTION_VIEW, uri))
        }
    }
}
