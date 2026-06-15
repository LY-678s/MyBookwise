package com.example.bookwiseapp.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.bookwiseapp.ui.component.*
import com.example.bookwiseapp.viewmodel.OrderViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OrderDetailScreen(
    orderId: Int,
    viewModel: OrderViewModel,
    onBack: () -> Unit
) {
    val state by viewModel.detailState.collectAsState()

    LaunchedEffect(orderId) { viewModel.loadOrderDetail(orderId) }

    // 操作成功后刷新
    LaunchedEffect(state.message) {
        if (state.message != null) {
            viewModel.loadOrderDetail(orderId)
            viewModel.clearDetailMessage()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("订单详情") },
                navigationIcon = { IconButton(onClick = onBack) {
                    Icon(Icons.Default.ArrowBack, "返回")
                }}
            )
        }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when {
                state.isLoading -> LoadingOverlay()
                state.error != null -> ErrorMessage(state.error!!, onRetry = { viewModel.loadOrderDetail(orderId) })
                state.order != null -> {
                    val order = state.order!!
                    Column(
                        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        // 基本信息
                        Card(Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(12.dp)) {
                                Text("订单信息", style = MaterialTheme.typography.titleSmall)
                                Spacer(Modifier.height(8.dp))
                                InfoRow("订单号", order.orderNo)
                                InfoRow("下单时间", order.orderDate?.take(16) ?: "")
                                InfoRow("收货地址", order.shipAddress)
                                InfoRow("订单状态", orderStatusText(order.status))
                                InfoRow("付款状态", paymentStatusText(order.paymentStatus))
                                InfoRow("应付金额", "¥${order.totalAmount}")
                                InfoRow("已付金额", "¥${order.actualPaid}")
                                if (order.unpaidAmount != "0.00") {
                                    InfoRow("待付金额", "¥${order.unpaidAmount}")
                                }
                                if (order.discountAmount != "0.00") {
                                    InfoRow("已优惠", "¥${order.discountAmount}")
                                }
                            }
                        }

                        // 商品明细
                        Card(Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(12.dp)) {
                                Text("商品明细", style = MaterialTheme.typography.titleSmall)
                                Spacer(Modifier.height(8.dp))
                                order.details?.forEach { detail ->
                                    Row(
                                        Modifier.fillMaxWidth().padding(vertical = 4.dp),
                                    ) {
                                        Column(Modifier.weight(1f)) {
                                            Text(detail.title,
                                                style = MaterialTheme.typography.bodyMedium)
                                            Text("单价 ¥${detail.unitPrice} × ${detail.quantity}",
                                                style = MaterialTheme.typography.bodySmall,
                                                color = MaterialTheme.colorScheme.outline)
                                        }
                                        Text("¥${detail.discountedAmount}",
                                            style = MaterialTheme.typography.bodyMedium,
                                            color = MaterialTheme.colorScheme.primary)
                                    }
                                    Divider()
                                }
                            }
                        }

                        // 操作按钮
                        state.error?.let {
                            Text(it, color = MaterialTheme.colorScheme.error,
                                style = MaterialTheme.typography.bodySmall)
                        }

                        // 补足支付（部分信用支付）
                        if (order.paymentStatus == 2 && order.status != 4) {
                            Button(
                                onClick = { viewModel.payOrder(orderId) },
                                enabled = !state.isLoading,
                                modifier = Modifier.fillMaxWidth()
                            ) { Text("补足支付 ¥${order.unpaidAmount}") }
                        }
                        // 取消订单
                        if (order.status == 0) {
                            OutlinedButton(
                                onClick = { viewModel.cancelOrder(orderId) },
                                enabled = !state.isLoading,
                                modifier = Modifier.fillMaxWidth()
                            ) { Text("取消订单") }
                        }
                        // 确认收货
                        if (order.status == 1) {
                            Button(
                                onClick = { viewModel.confirmReceipt(orderId) },
                                enabled = !state.isLoading,
                                modifier = Modifier.fillMaxWidth()
                            ) { Text("确认收货") }
                        }
                    }
                }
            }
        }
    }
}
