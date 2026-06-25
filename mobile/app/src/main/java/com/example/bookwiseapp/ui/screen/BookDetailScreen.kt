package com.example.bookwiseapp.ui.screen

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.FavoriteBorder
import androidx.compose.material.icons.filled.ShoppingCart
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
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
    var showFolderPicker by remember { mutableStateOf(false) }
    var showCreateFolder by remember { mutableStateOf(false) }
    var newFolderName by remember { mutableStateOf("") }

    LaunchedEffect(isbn) { viewModel.loadBookDetail(isbn) }

    if (showSnack && cartState.message != null) {
        LaunchedEffect(cartState.message) {
            showSnack = false
            cartVm.clearMessage()
        }
    }

    Scaffold(
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
        topBar = {
            TopAppBar(
                title = { Text("图书详情") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, "返回")
                    }
                },
                actions = {
                    if (state.book != null) {
                        IconButton(
                            onClick = {
                                if (state.isFavorited) {
                                    viewModel.toggleFavorite(isbn)
                                } else {
                                    showFolderPicker = true
                                }
                            },
                            enabled = !state.favoriteLoading
                        ) {
                            Icon(
                                if (state.isFavorited) Icons.Default.Favorite else Icons.Default.FavoriteBorder,
                                contentDescription = "收藏",
                                tint = if (state.isFavorited) MaterialTheme.colorScheme.error
                                else MaterialTheme.colorScheme.onSurface
                            )
                        }
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
                        Box(
                            Modifier
                                .fillMaxWidth()
                                .height(300.dp)
                                .background(MaterialTheme.colorScheme.surfaceVariant),
                            contentAlignment = Alignment.Center
                        ) {
                            BookCover(
                                book = book,
                                modifier = Modifier
                                    .fillMaxHeight()
                                    .padding(horizontal = 24.dp, vertical = 12.dp),
                                defaultCoverUrl = state.defaultCoverUrl,
                                contentScale = ContentScale.Fit
                            )
                        }
                        Column(Modifier.padding(16.dp)) {
                            Text(book.title, style = MaterialTheme.typography.headlineSmall)
                            Spacer(Modifier.height(4.dp))
                            Text(
                                "¥${book.price}",
                                style = MaterialTheme.typography.titleLarge,
                                color = MaterialTheme.colorScheme.primary
                            )
                            Spacer(Modifier.height(12.dp))
                            HorizontalDivider()
                            Spacer(Modifier.height(12.dp))

                            book.authors?.let {
                                InfoRow("作者", it.joinToString("、"))
                            }
                            book.publisher?.let { InfoRow("出版社", it) }
                            InfoRow("ISBN", book.isbn)
                            book.keywords?.let { InfoRow("关键字", it) }
                            InfoRow("库存", "${book.stockQty} 本")
                            book.location?.let { InfoRow("位置", it) }
                            if (state.favoriteCount > 0) {
                                InfoRow("收藏", "${state.favoriteCount} 人")
                            }
                            state.favoriteMessage?.let {
                                Spacer(Modifier.height(8.dp))
                                Text(
                                    it,
                                    color = MaterialTheme.colorScheme.primary,
                                    style = MaterialTheme.typography.bodySmall
                                )
                            }

                            Spacer(Modifier.height(16.dp))
                            HorizontalDivider()
                            Spacer(Modifier.height(16.dp))

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

    if (showFolderPicker) {
        AlertDialog(
            onDismissRequest = { showFolderPicker = false },
            title = { Text("选择收藏夹") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    state.favoriteFolders.forEach { folder ->
                        TextButton(
                            onClick = {
                                viewModel.toggleFavorite(isbn, folder.id)
                                showFolderPicker = false
                            },
                            modifier = Modifier.fillMaxWidth()
                        ) { Text(folder.name) }
                    }
                    HorizontalDivider(Modifier.padding(vertical = 4.dp))
                    TextButton(
                        onClick = {
                            showFolderPicker = false
                            showCreateFolder = true
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) { Text("新建收藏夹…") }
                }
            },
            confirmButton = {},
            dismissButton = {
                TextButton(onClick = { showFolderPicker = false }) { Text("取消") }
            }
        )
    }

    if (showCreateFolder) {
        AlertDialog(
            onDismissRequest = { showCreateFolder = false; newFolderName = "" },
            title = { Text("新建收藏夹") },
            text = {
                OutlinedTextField(
                    value = newFolderName,
                    onValueChange = { newFolderName = it },
                    label = { Text("名称") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        val name = newFolderName.trim()
                        if (name.isNotBlank()) {
                            viewModel.createFavoriteFolder(name) { folder ->
                                viewModel.toggleFavorite(isbn, folder.id)
                            }
                            showCreateFolder = false
                            newFolderName = ""
                        }
                    },
                    enabled = newFolderName.isNotBlank()
                ) { Text("创建并收藏") }
            },
            dismissButton = {
                TextButton(onClick = { showCreateFolder = false; newFolderName = "" }) { Text("取消") }
            }
        )
    }
}
