package com.example.bookwiseapp.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.bookwiseapp.ui.component.ErrorMessage
import com.example.bookwiseapp.ui.component.LoadingOverlay
import com.example.bookwiseapp.ui.component.orderStatusText
import com.example.bookwiseapp.ui.component.paymentStatusText
import com.example.bookwiseapp.viewmodel.OrderViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OrderListScreen(
    viewModel: OrderViewModel,
    onOrderClick: (Int) -> Unit,
    onBack: (() -> Unit)? = null
) {
    val state by viewModel.listState.collectAsState()

    LaunchedEffect(Unit) { viewModel.loadOrders() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("我的订单") },
                navigationIcon = {
                    if (onBack != null) {
                        IconButton(onClick = onBack) {
                            Icon(Icons.Default.ArrowBack, contentDescription = "返回")
                        }
                    }
                }
            )
        }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when {
                state.isLoading && state.orders.isEmpty() -> LoadingOverlay()
                state.error != null && state.orders.isEmpty() ->
                    ErrorMessage(state.error!!, onRetry = { viewModel.loadOrders() })
                else ->
                    PullToRefreshBox(
                        isRefreshing = state.isLoading,
                        onRefresh = { viewModel.loadOrders() },
                        modifier = Modifier.fillMaxSize()
                    ) {
                        if (state.orders.isEmpty()) {
                            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                                Text("暂无订单", color = MaterialTheme.colorScheme.outline)
                            }
                        } else {
                            LazyColumn(
                                modifier = Modifier.fillMaxSize(),
                                contentPadding = PaddingValues(12.dp),
                                verticalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                items(state.orders, key = { it.orderId }) { order ->
                                    Card(
                                        modifier = Modifier.fillMaxWidth(),
                                        onClick = { onOrderClick(order.orderId) }
                                    ) {
                                        Column(Modifier.padding(12.dp)) {
                                            Row(
                                                Modifier.fillMaxWidth(),
                                                horizontalArrangement = Arrangement.SpaceBetween
                                            ) {
                                                Text(order.orderNo,
                                                    style = MaterialTheme.typography.labelMedium,
                                                    color = MaterialTheme.colorScheme.outline)
                                                val statusColor = when (order.status) {
                                                    2 -> MaterialTheme.colorScheme.secondary
                                                    4 -> MaterialTheme.colorScheme.outline
                                                    else -> MaterialTheme.colorScheme.primary
                                                }
                                                Text(orderStatusText(order.status),
                                                    style = MaterialTheme.typography.labelSmall,
                                                    color = statusColor)
                                            }
                                            Spacer(Modifier.height(6.dp))
                                            order.details?.take(2)?.forEach { detail ->
                                                Text("${detail.title} ×${detail.quantity}",
                                                    style = MaterialTheme.typography.bodySmall,
                                                    color = MaterialTheme.colorScheme.onSurfaceVariant)
                                            }
                                            if ((order.details?.size ?: 0) > 2) {
                                                Text("等 ${order.details!!.size} 件商品",
                                                    style = MaterialTheme.typography.labelSmall,
                                                    color = MaterialTheme.colorScheme.outline)
                                            }
                                            Spacer(Modifier.height(6.dp))
                                            Row(
                                                Modifier.fillMaxWidth(),
                                                horizontalArrangement = Arrangement.SpaceBetween,
                                                verticalAlignment = Alignment.CenterVertically
                                            ) {
                                                Text(paymentStatusText(order.paymentStatus),
                                                    style = MaterialTheme.typography.labelSmall,
                                                    color = if (order.paymentStatus == 1)
                                                        MaterialTheme.colorScheme.secondary
                                                    else MaterialTheme.colorScheme.error)
                                                Text("¥${order.totalAmount}",
                                                    style = MaterialTheme.typography.titleSmall,
                                                    color = MaterialTheme.colorScheme.primary)
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
            }
        }
    }
}
