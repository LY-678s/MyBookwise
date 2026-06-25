package com.example.bookwiseapp.util

/** Stripe Checkout 回调 deep link（与后端 create_order / membership checkout 配合）。 */
object StripeDeepLink {
    const val SCHEME = "bookwise"
    const val HOST = "pay"

    /** 下单成功；`{order_id}` 由服务端替换。 */
    fun orderSuccessUrl() =
        "$SCHEME://$HOST/order/success?session_id={CHECKOUT_SESSION_ID}&order_id={order_id}"

    /** 下单取消；`{order_id}` 由服务端替换。 */
    fun orderCancelUrl() =
        "$SCHEME://$HOST/order/cancel?order_id={order_id}"

    fun membershipSuccessUrl() =
        "$SCHEME://$HOST/membership/success?session_id={CHECKOUT_SESSION_ID}"

    fun membershipCancelUrl() =
        "$SCHEME://$HOST/membership/cancel"
}

sealed class PaymentDeepLink {
    data class OrderSuccess(val sessionId: String, val orderId: Int) : PaymentDeepLink()
    data class OrderCancel(val orderId: Int) : PaymentDeepLink()
    data class MembershipSuccess(val sessionId: String) : PaymentDeepLink()
    data object MembershipCancel : PaymentDeepLink()
}

fun parsePaymentDeepLink(uri: android.net.Uri?): PaymentDeepLink? {
    if (uri == null || uri.scheme != StripeDeepLink.SCHEME || uri.host != StripeDeepLink.HOST) {
        return null
    }
    val segments = uri.pathSegments
    if (segments.size < 2) return null
    return when ("${segments[0]}/${segments[1]}") {
        "order/success" -> {
            val sessionId = uri.getQueryParameter("session_id") ?: return null
            val orderId = uri.getQueryParameter("order_id")?.toIntOrNull() ?: return null
            PaymentDeepLink.OrderSuccess(sessionId, orderId)
        }
        "order/cancel" -> {
            val orderId = uri.getQueryParameter("order_id")?.toIntOrNull() ?: return null
            PaymentDeepLink.OrderCancel(orderId)
        }
        "membership/success" -> {
            val sessionId = uri.getQueryParameter("session_id") ?: return null
            PaymentDeepLink.MembershipSuccess(sessionId)
        }
        "membership/cancel" -> PaymentDeepLink.MembershipCancel
        else -> null
    }
}
