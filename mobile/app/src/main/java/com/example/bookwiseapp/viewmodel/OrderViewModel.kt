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
        paymentChoice: String,
        shippingName: String,
        shippingContact: String,
        shippingAddress: String,
        onSuccess: (Int) -> Unit
    ) {
        viewModelScope.launch {
            _checkoutState.value = _checkoutState.value.copy(isLoading = true, error = null)
            val result = repo.createOrder(paymentChoice, shippingName, shippingContact, shippingAddress)
            if (result.isSuccess) {
                val order = result.getOrNull()?.order
                _checkoutState.value = _checkoutState.value.copy(isLoading = false, orderCreated = order)
                order?.let { onSuccess(it.orderId) }
            } else {
                _checkoutState.value = _checkoutState.value.copy(
                    isLoading = false,
                    error = result.exceptionOrNull()?.message
                )
            }
        }
    }

    fun payOrder(orderId: Int) {
        viewModelScope.launch {
            _detailState.value = _detailState.value.copy(isLoading = true)
            val result = repo.payOrder(orderId)
            handleOrderAction(result)
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
