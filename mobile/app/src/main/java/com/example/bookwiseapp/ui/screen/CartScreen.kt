package com.example.bookwiseapp.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.*
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.bookwiseapp.ui.component.BookCover
import com.example.bookwiseapp.ui.component.ErrorMessage
import com.example.bookwiseapp.ui.component.LoadingOverlay
import com.example.bookwiseapp.viewmodel.CartViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CartScreen(
    viewModel: CartViewModel,
    onCheckout: () -> Unit
) {
    val state by viewModel.state.collectAsState()

    LaunchedEffect(Unit) { viewModel.loadCart() }

    Scaffold(
        topBar = { TopAppBar(title = { Text("购物车") }) }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when {
                state.isLoading && state.cart == null -> LoadingOverlay()
                state.error != null && state.cart == null ->
                    ErrorMessage(state.error!!, onRetry = { viewModel.loadCart() })
                else -> {
                    val cart = state.cart
                    if (cart == null || cart.items.isEmpty()) {
                        PullToRefreshBox(
                            isRefreshing = state.isLoading,
                            onRefresh = { viewModel.loadCart() },
                            modifier = Modifier.fillMaxSize()
                        ) {
                            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                                Text("购物车是空的", color = MaterialTheme.colorScheme.outline)
                            }
                        }
                    } else {
                        Column(Modifier.fillMaxSize()) {
                            PullToRefreshBox(
                                isRefreshing = state.isLoading,
                                onRefresh = { viewModel.loadCart() },
                                modifier = Modifier.weight(1f)
                            ) {
                                LazyColumn(
                                    modifier = Modifier.fillMaxSize(),
                                    contentPadding = PaddingValues(12.dp),
                                    verticalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    items(cart.items, key = { it.book.isbn }) { item ->
                                        Card(Modifier.fillMaxWidth()) {
                                            Row(
                                                Modifier.padding(12.dp),
                                                verticalAlignment = Alignment.CenterVertically
                                            ) {
                                                BookCover(
                                                    book = item.book,
                                                    modifier = Modifier.size(56.dp, 72.dp)
                                                )
                                                Spacer(Modifier.width(12.dp))
                                                Column(Modifier.weight(1f)) {
                                                    Text(item.book.title,
                                                        style = MaterialTheme.typography.bodyMedium,
                                                        maxLines = 2)
                                                    Text("¥${item.book.price} × ${item.quantity}",
                                                        style = MaterialTheme.typography.bodySmall,
                                                        color = MaterialTheme.colorScheme.outline)
                                                    Text("小计 ¥${item.discountedAmount}",
                                                        style = MaterialTheme.typography.labelMedium,
                                                        color = MaterialTheme.colorScheme.primary)
                                                }
                                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                                        IconButton(
                                                            onClick = {
                                                                val q = item.quantity - 1
                                                                if (q > 0) viewModel.updateItem(item.book.isbn, q)
                                                                else viewModel.removeItem(item.book.isbn)
                                                            },
                                                            modifier = Modifier.size(32.dp)
                                                        ) { Text("−") }
                                                        Text(item.quantity.toString(),
                                                            modifier = Modifier.padding(horizontal = 4.dp))
                                                        IconButton(
                                                            onClick = { viewModel.updateItem(item.book.isbn, item.quantity + 1) },
                                                            modifier = Modifier.size(32.dp)
                                                        ) { Text("+") }
                                                    }
                                                    IconButton(
                                                        onClick = { viewModel.removeItem(item.book.isbn) },
                                                        modifier = Modifier.size(32.dp)
                                                    ) {
                                                        Icon(Icons.Default.Delete, "删除",
                                                            tint = MaterialTheme.colorScheme.error,
                                                            modifier = Modifier.size(18.dp))
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }

                            // 底部结算栏
                            Surface(
                                shadowElevation = 8.dp,
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Row(
                                    Modifier.padding(16.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Column(Modifier.weight(1f)) {
                                        if (cart.discountAmount != "0.00") {
                                            Text(
                                                "折扣 ${cart.discountPercent}%",
                                                style = MaterialTheme.typography.labelSmall,
                                                color = MaterialTheme.colorScheme.outline
                                            )
                                        }
                                        Row {
                                            Text("合计 ", style = MaterialTheme.typography.bodyMedium)
                                            Text("¥${cart.discountedTotal}",
                                                style = MaterialTheme.typography.titleMedium,
                                                color = MaterialTheme.colorScheme.primary)
                                        }
                                        if (cart.discountAmount != "0.00") {
                                            Text("节省 ¥${cart.discountAmount}",
                                                style = MaterialTheme.typography.labelSmall,
                                                color = MaterialTheme.colorScheme.secondary)
                                        }
                                    }
                                    Button(
                                        onClick = onCheckout,
                                        modifier = Modifier.height(44.dp)
                                    ) { Text("去结算 (${cart.items.size})") }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
