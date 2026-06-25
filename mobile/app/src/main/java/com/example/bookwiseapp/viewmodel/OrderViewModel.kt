package com.example.bookwiseapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.bookwiseapp.data.api.model.CartData
import com.example.bookwiseapp.data.api.model.OrderData
import com.example.bookwiseapp.data.repository.OrderRepository
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
    val preview: CartData? = null,
    val error: String? = null,
    val orderCreated: OrderData? = null
)

class OrderViewModel : ViewModel() {

    private val repo = OrderRepository()

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

    fun loadCheckoutPreview() {
        viewModelScope.launch {
            _checkoutState.value = CheckoutUiState(isLoading = true)
            val result = repo.preview()
            if (result.isSuccess) {
                _checkoutState.value = CheckoutUiState(preview = result.getOrNull()?.preview)
            } else {
                _checkoutState.value = CheckoutUiState(error = result.exceptionOrNull()?.message)
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
                    orderCreated = data.order
                )
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
        onSuccess: (orderId: Int, message: String?) -> Unit,
        onError: (String) -> Unit
    ) {
        viewModelScope.launch {
            val result = repo.confirmPayment(sessionId)
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                val orderId = data.orderId
                if (orderId != null) {
                    onSuccess(orderId, data.message)
                } else {
                    onError("支付成功但未返回订单号")
                }
            } else {
                onError(result.exceptionOrNull()?.message ?: "支付确认失败")
            }
        }
    }

    fun abandonCheckoutOrder(
        orderId: Int,
        onDone: (String?) -> Unit
    ) {
        viewModelScope.launch {
            val result = repo.abandonOrder(orderId)
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
