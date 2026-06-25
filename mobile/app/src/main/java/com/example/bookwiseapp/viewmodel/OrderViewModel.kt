package com.example.bookwiseapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.bookwiseapp.data.api.model.CartData
import com.example.bookwiseapp.data.api.model.CustomerData
import com.example.bookwiseapp.data.api.model.OrderData
import com.example.bookwiseapp.data.api.model.PaymentConfirmResponse
import com.example.bookwiseapp.data.local.PendingPaymentStore
import com.example.bookwiseapp.data.repository.OrderRepository
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class OrderListUiState(
    val isLoading: Boolean = false,
    val orders: List<OrderData> = emptyList(),
    val error: String? = null
)

data class OrderDetailUiState(
    val isLoading: Boolean = false,
    val order: OrderData? = null,
    val message: String? = null,
    val error: String? = null
)

data class CheckoutUiState(
    val isLoading: Boolean = false,
    val isConfirmingPayment: Boolean = false,
    val preview: CartData? = null,
    val error: String? = null,
    val paymentError: String? = null,
    val orderCreated: OrderData? = null,
    val pendingSessionId: String? = null,
    val pendingOrderId: Int? = null
)

class OrderViewModel : ViewModel() {

    private val repo = OrderRepository()
    private val pendingStore = PendingPaymentStore.instance
    private var paymentRecoveryRunning = false

    private val _listState = MutableStateFlow(OrderListUiState())
    val listState: StateFlow<OrderListUiState> = _listState

    private val _detailState = MutableStateFlow(OrderDetailUiState())
    val detailState: StateFlow<OrderDetailUiState> = _detailState

    private val _checkoutState = MutableStateFlow(CheckoutUiState())
    val checkoutState: StateFlow<CheckoutUiState> = _checkoutState

    fun loadOrders() {
        viewModelScope.launch {
            _listState.value = OrderListUiState(isLoading = true)
            val result = repo.listOrders()
            if (result.isSuccess) {
                _listState.value = OrderListUiState(orders = result.getOrNull()?.orders ?: emptyList())
            } else {
                _listState.value = OrderListUiState(error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun loadOrderDetail(orderId: Int) {
        viewModelScope.launch {
            _detailState.value = OrderDetailUiState(isLoading = true)
            val result = repo.getOrder(orderId)
            if (result.isSuccess) {
                _detailState.value = OrderDetailUiState(order = result.getOrNull()?.order)
            } else {
                _detailState.value = OrderDetailUiState(error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun clearCheckoutAfterPayment() {
        _checkoutState.value = CheckoutUiState()
    }

    /** 进入确认订单页：清空上次残留状态并拉取预览。 */
    fun beginCheckout(onEmptyCart: () -> Unit = {}) {
        viewModelScope.launch {
            _checkoutState.value = CheckoutUiState(isLoading = true)
            val result = repo.preview()
            if (result.isSuccess) {
                _checkoutState.value = CheckoutUiState(
                    preview = result.getOrNull()?.preview
                )
            } else {
                val msg = result.exceptionOrNull()?.message
                if (msg == "购物车为空") {
                    _checkoutState.value = CheckoutUiState()
                    onEmptyCart()
                } else {
                    _checkoutState.value = CheckoutUiState(error = msg)
                }
            }
        }
    }

    fun loadCheckoutPreview() {
        viewModelScope.launch {
            _checkoutState.value = _checkoutState.value.copy(isLoading = true, error = null)
            val result = repo.preview()
            if (result.isSuccess) {
                _checkoutState.value = _checkoutState.value.copy(
                    isLoading = false,
                    preview = result.getOrNull()?.preview,
                    error = null
                )
            } else {
                val msg = result.exceptionOrNull()?.message
                _checkoutState.value = _checkoutState.value.copy(
                    isLoading = false,
                    error = if (msg == "购物车为空") null else msg
                )
            }
        }
    }

    fun createOrder(
        shippingName: String,
        shippingContact: String,
        shippingAddress: String,
        onStripeUrl: (String) -> Unit
    ) {
        viewModelScope.launch {
            _checkoutState.value = _checkoutState.value.copy(isLoading = true, error = null)
            val result = repo.createOrder(shippingName, shippingContact, shippingAddress)
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                val url = data.checkoutUrl
                _checkoutState.value = _checkoutState.value.copy(
                    isLoading = false,
                    orderCreated = data.order,
                    pendingSessionId = data.sessionId,
                    pendingOrderId = data.order?.orderId
                )
                val sid = data.sessionId
                val oid = data.order?.orderId
                if (!sid.isNullOrBlank() && oid != null) {
                    pendingStore.save(sid, oid)
                }
                if (!url.isNullOrBlank()) {
                    onStripeUrl(url)
                } else {
                    _checkoutState.value = _checkoutState.value.copy(
                        error = "未获取到支付链接"
                    )
                }
            } else {
                _checkoutState.value = _checkoutState.value.copy(
                    isLoading = false,
                    error = result.exceptionOrNull()?.message
                )
            }
        }
    }

    fun confirmStripePayment(
        sessionId: String,
        orderIdHint: Int? = null,
        onSuccess: (orderId: Int, message: String?, account: CustomerData?) -> Unit,
        onError: (String) -> Unit
    ) {
        viewModelScope.launch {
            recoverPendingPayment(
                sessionId = sessionId,
                orderIdHint = orderIdHint ?: _checkoutState.value.pendingOrderId,
                onSuccess = onSuccess,
                onError = onError
            )
        }
    }

    /**
     * Stripe 支付后确认：先 confirm，失败则 sync；支持进程恢复与 deep link 缺失 order_id。
     */
    fun recoverPendingPayment(
        sessionId: String? = null,
        orderIdHint: Int? = null,
        onSuccess: (orderId: Int, message: String?, account: CustomerData?) -> Unit,
        onError: (String) -> Unit = {},
        onSkip: () -> Unit = {}
    ) {
        viewModelScope.launch {
            if (paymentRecoveryRunning) return@launch
            val stored = pendingStore.load()
            val sid = sessionId?.takeIf { it.isNotBlank() }
                ?: _checkoutState.value.pendingSessionId
                ?: stored?.sessionId
            if (sid.isNullOrBlank()) {
                onSkip()
                return@launch
            }
            val orderId = orderIdHint
                ?: _checkoutState.value.pendingOrderId
                ?: stored?.orderId

            paymentRecoveryRunning = true
            _checkoutState.value = _checkoutState.value.copy(
                isConfirmingPayment = true,
                paymentError = null
            )
            try {
                val confirmResult = confirmWithRetry(sid)
                if (confirmResult.isSuccess) {
                    applyPaymentSuccess(confirmResult.getOrNull()!!, onSuccess, onError)
                    return@launch
                }
                if (orderId != null) {
                    val syncResult = repo.syncOrderPayment(orderId)
                    if (syncResult.isSuccess) {
                        applyPaymentSuccess(syncResult.getOrNull()!!, onSuccess, onError)
                        return@launch
                    }
                    val err = syncResult.exceptionOrNull()?.message
                        ?: confirmResult.exceptionOrNull()?.message
                        ?: "支付确认失败"
                    _checkoutState.value = _checkoutState.value.copy(paymentError = err)
                    onError(err)
                } else {
                    val err = confirmResult.exceptionOrNull()?.message ?: "支付确认失败"
                    _checkoutState.value = _checkoutState.value.copy(paymentError = err)
                    onError(err)
                }
            } finally {
                paymentRecoveryRunning = false
                _checkoutState.value = _checkoutState.value.copy(isConfirmingPayment = false)
            }
        }
    }

    private suspend fun confirmWithRetry(sessionId: String, attempts: Int = 6): Result<PaymentConfirmResponse> {
        var last: Result<PaymentConfirmResponse> = Result.failure(Exception("支付确认失败"))
        repeat(attempts) { attempt ->
            last = repo.confirmPayment(sessionId)
            if (last.isSuccess) return last
            if (attempt < attempts - 1) delay(2000L)
        }
        return last
    }

    private suspend fun applyPaymentSuccess(
        data: PaymentConfirmResponse,
        onSuccess: (orderId: Int, message: String?, account: CustomerData?) -> Unit,
        onError: (String) -> Unit = {}
    ) {
        val orderId = data.orderId ?: data.order?.orderId
        pendingStore.clear()
        _checkoutState.value = CheckoutUiState()
        if (orderId != null) {
            onSuccess(orderId, data.message, data.account)
        } else {
            onError("支付成功但未返回订单号")
        }
    }

    fun tryRecoverStoredPayment(
        onSuccess: (orderId: Int, message: String?, account: CustomerData?) -> Unit,
        onSkip: () -> Unit = {}
    ) {
        recoverPendingPayment(onSuccess = onSuccess, onSkip = onSkip)
    }

    fun syncOrderPayment(
        orderId: Int,
        onSuccess: (message: String?, account: CustomerData?, order: OrderData?) -> Unit,
        onError: (String) -> Unit
    ) {
        viewModelScope.launch {
            _detailState.value = _detailState.value.copy(isLoading = true, error = null)
            val result = repo.syncOrderPayment(orderId)
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                _detailState.value = OrderDetailUiState(
                    order = data.order,
                    message = data.message
                )
                if (data.order?.paymentStatus == 1) {
                    pendingStore.clear()
                }
                onSuccess(data.message, data.account, data.order)
            } else {
                _detailState.value = _detailState.value.copy(
                    isLoading = false,
                    error = result.exceptionOrNull()?.message ?: "同步失败"
                )
                onError(_detailState.value.error!!)
            }
        }
    }

    fun clearPendingPayment() {
        viewModelScope.launch {
            pendingStore.clear()
        }
        _checkoutState.value = _checkoutState.value.copy(
            pendingSessionId = null,
            pendingOrderId = null
        )
    }

    fun abandonCheckoutOrder(
        orderId: Int,
        onDone: (String?) -> Unit
    ) {
        viewModelScope.launch {
            val result = repo.abandonOrder(orderId)
            if (result.isSuccess) {
                pendingStore.clear()
                _checkoutState.value = _checkoutState.value.copy(
                    pendingSessionId = null,
                    pendingOrderId = null
                )
            }
            onDone(if (result.isSuccess) result.getOrNull()?.message else result.exceptionOrNull()?.message)
        }
    }

    fun cancelOrder(orderId: Int) {
        viewModelScope.launch {
            _detailState.value = _detailState.value.copy(isLoading = true)
            val result = repo.cancelOrder(orderId)
            handleOrderAction(result)
        }
    }

    fun confirmReceipt(orderId: Int) {
        viewModelScope.launch {
            _detailState.value = _detailState.value.copy(isLoading = true)
            val result = repo.confirmReceipt(orderId)
            handleOrderAction(result)
        }
    }

    private fun handleOrderAction(result: Result<com.example.bookwiseapp.data.api.model.OrderResponse>) {
        if (result.isSuccess) {
            val data = result.getOrNull()!!
            _detailState.value = OrderDetailUiState(order = data.order, message = data.message)
        } else {
            _detailState.value = _detailState.value.copy(
                isLoading = false,
                error = result.exceptionOrNull()?.message
            )
        }
    }

    fun clearDetailMessage() {
        _detailState.value = _detailState.value.copy(message = null, error = null)
    }
}
