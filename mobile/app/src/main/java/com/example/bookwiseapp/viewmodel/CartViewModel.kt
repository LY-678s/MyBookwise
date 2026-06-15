package com.example.bookwiseapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.bookwiseapp.data.api.model.CartData
import com.example.bookwiseapp.data.repository.CartRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class CartUiState(
    val isLoading: Boolean = false,
    val cart: CartData? = null,
    val message: String? = null,
    val error: String? = null
)

class CartViewModel : ViewModel() {

    private val repo = CartRepository()

    private val _state = MutableStateFlow(CartUiState())
    val state: StateFlow<CartUiState> = _state

    fun loadCart() {
        viewModelScope.launch {
            _state.value = _state.value.copy(isLoading = true, error = null, message = null)
            val result = repo.getCart()
            if (result.isSuccess) {
                _state.value = CartUiState(cart = result.getOrNull()?.cart)
            } else {
                _state.value = CartUiState(error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun addToCart(isbn: String, quantity: Int = 1) {
        viewModelScope.launch {
            val result = repo.addToCart(isbn, quantity)
            if (result.isSuccess) {
                _state.value = CartUiState(
                    cart = result.getOrNull()?.cart,
                    message = result.getOrNull()?.message
                )
            } else {
                _state.value = _state.value.copy(error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun updateItem(isbn: String, quantity: Int) {
        viewModelScope.launch {
            val result = repo.updateItem(isbn, quantity)
            if (result.isSuccess) {
                _state.value = CartUiState(cart = result.getOrNull()?.cart)
            } else {
                _state.value = _state.value.copy(error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun removeItem(isbn: String) {
        viewModelScope.launch {
            val result = repo.removeItem(isbn)
            if (result.isSuccess) {
                _state.value = CartUiState(cart = result.getOrNull()?.cart)
            } else {
                _state.value = _state.value.copy(error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun clearMessage() {
        _state.value = _state.value.copy(message = null, error = null)
    }
}
