package com.example.bookwiseapp.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.ShoppingCart
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.bookwiseapp.ui.component.BookCover
import com.example.bookwiseapp.ui.component.ErrorMessage
import com.example.bookwiseapp.ui.component.InfoRow
import com.example.bookwiseapp.ui.component.LoadingOverlay
import com.example.bookwiseapp.viewmodel.BookViewModel
import com.example.bookwiseapp.viewmodel.CartViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BookDetailScreen(
    isbn: String,
    viewModel: BookViewModel,
    cartVm: CartViewModel,
    onBack: () -> Unit
) {
    val state by viewModel.detailState.collectAsState()
    val cartState by cartVm.state.collectAsState()

    var quantity by remember { mutableIntStateOf(1) }
    var showSnack by remember { mutableStateOf(false) }

    LaunchedEffect(isbn) { viewModel.loadBookDetail(isbn) }

    // 加入购物车后提示
    if (showSnack && cartState.message != null) {
        LaunchedEffect(cartState.message) {
            showSnack = false
            cartVm.clearMessage()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(state.book?.title ?: "图书详情") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, "返回")
                    }
                }
            )
        }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when {
                state.isLoading -> LoadingOverlay()
                state.error != null -> ErrorMessage(state.error!!, onRetry = { viewModel.loadBookDetail(isbn) })
                state.book != null -> {
                    val book = state.book!!
                    Column(
                        Modifier.fillMaxSize().verticalScroll(rememberScrollState())
                    ) {
                        // 封面
                        BookCover(
                            book = book,
                            modifier = Modifier.fillMaxWidth().height(240.dp)
                        )
                        Column(Modifier.padding(16.dp)) {
                            Text(book.title, style = MaterialTheme.typography.headlineSmall)
                            Spacer(Modifier.height(4.dp))
                            Text(
                                "¥${book.price}",
                                style = MaterialTheme.typography.titleLarge,
                                color = MaterialTheme.colorScheme.primary
                            )
                            Spacer(Modifier.height(12.dp))
                            Divider()
                            Spacer(Modifier.height(12.dp))

                            book.authors?.let {
                                InfoRow("作者", it.joinToString("、"))
                            }
                            book.publisher?.let { InfoRow("出版社", it) }
                            InfoRow("ISBN", book.isbn)
                            book.keywords?.let { InfoRow("关键字", it) }
                            InfoRow("库存", "${book.stockQty} 本")
                            book.location?.let { InfoRow("位置", it) }

                            Spacer(Modifier.height(16.dp))
                            Divider()
                            Spacer(Modifier.height(16.dp))

                            // 数量选择
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(12.dp)
                            ) {
                                Text("数量", style = MaterialTheme.typography.bodyLarge)
                                IconButton(
                                    onClick = { if (quantity > 1) quantity-- },
                                    enabled = quantity > 1
                                ) { Text("−", style = MaterialTheme.typography.titleMedium) }
                                Text(quantity.toString(), style = MaterialTheme.typography.titleMedium)
                                IconButton(
                                    onClick = { if (quantity < book.stockQty) quantity++ },
                                    enabled = quantity < book.stockQty
                                ) { Text("+", style = MaterialTheme.typography.titleMedium) }
                            }

                            Spacer(Modifier.height(12.dp))
                            Button(
                                onClick = {
                                    cartVm.addToCart(isbn, quantity)
                                    showSnack = true
                                },
                                enabled = book.stockQty > 0 && !cartState.isLoading,
                                modifier = Modifier.fillMaxWidth().height(48.dp)
                            ) {
                                Icon(Icons.Default.ShoppingCart, null)
                                Spacer(Modifier.width(8.dp))
                                Text(if (book.stockQty == 0) "暂无库存" else "加入购物车")
                            }

                            cartState.message?.let {
                                Spacer(Modifier.height(8.dp))
                                Text(it, color = MaterialTheme.colorScheme.primary,
                                    style = MaterialTheme.typography.bodySmall)
                            }
                            cartState.error?.let {
                                Spacer(Modifier.height(8.dp))
                                Text(it, color = MaterialTheme.colorScheme.error,
                                    style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    }
                }
            }
        }
    }
}
