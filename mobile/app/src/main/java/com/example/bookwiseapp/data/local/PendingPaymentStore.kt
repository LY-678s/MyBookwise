package com.example.bookwiseapp.data.local

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.pendingPaymentDataStore by preferencesDataStore(name = "bookwise_pending_payment")

/** Stripe 跳转支付后待确认的 session / 订单（进程被杀或 deep link 失败时可恢复）。 */
class PendingPaymentStore(private val context: Context) {

    data class Pending(val sessionId: String, val orderId: Int)

    companion object {
        private val KEY_SESSION = stringPreferencesKey("stripe_session_id")
        private val KEY_ORDER = intPreferencesKey("pending_order_id")

        lateinit var instance: PendingPaymentStore
            private set

        fun init(context: Context) {
            instance = PendingPaymentStore(context)
        }
    }

    suspend fun save(sessionId: String, orderId: Int) {
        context.pendingPaymentDataStore.edit {
            it[KEY_SESSION] = sessionId
            it[KEY_ORDER] = orderId
        }
    }

    suspend fun clear() {
        context.pendingPaymentDataStore.edit {
            it.remove(KEY_SESSION)
            it.remove(KEY_ORDER)
        }
    }

    suspend fun load(): Pending? {
        val prefs = context.pendingPaymentDataStore.data.first()
        val sessionId = prefs[KEY_SESSION] ?: return null
        val orderId = prefs[KEY_ORDER] ?: return null
        return Pending(sessionId, orderId)
    }

    suspend fun sessionIdOrNull(): String? =
        context.pendingPaymentDataStore.data.map { it[KEY_SESSION] }.first()
}
