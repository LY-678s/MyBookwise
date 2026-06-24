package com.example.bookwiseapp.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Category
import androidx.compose.material.icons.filled.Leaderboard
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import com.example.bookwiseapp.ui.component.BookCover
import com.example.bookwiseapp.ui.component.ErrorMessage
import com.example.bookwiseapp.ui.component.LoadingOverlay
import com.example.bookwiseapp.viewmodel.BookViewModel
import com.example.bookwiseapp.viewmodel.CartViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SearchScreen(
    viewModel: BookViewModel,
    cartVm: CartViewModel,
    onBookClick: (String) -> Unit,
    onCategoriesClick: () -> Unit = {},
    onRankingsClick: () -> Unit = {}
) {
    val state by viewModel.searchState.collectAsState()
    var query by remember { mutableStateOf("") }

    Scaffold(
        topBar = { TopAppBar(title = { Text("搜索与发现") }) }
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            OutlinedTextField(
                value = query,
                onValueChange = { query = it },
                modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 8.dp),
                placeholder = { Text("书名 / ISBN / 关键字") },
                leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
                singleLine = true,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
                keyboardActions = KeyboardActions(onSearch = {
                    if (query.isNotBlank()) viewModel.searchBooks(query.trim())
                })
            )

            Row(
                Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 12.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                ElevatedCard(
                    onClick = onCategoriesClick,
                    modifier = Modifier.weight(1f)
                ) {
                    Row(
                        Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Icon(Icons.Default.Category, contentDescription = null)
                        Column {
                            Text("书籍分区", style = MaterialTheme.typography.titleSmall)
                            Text(
                                "按分类浏览",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.outline
                            )
                        }
                    }
                }
                ElevatedCard(
                    onClick = onRankingsClick,
                    modifier = Modifier.weight(1f)
                ) {
                    Row(
                        Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Icon(Icons.Default.Leaderboard, contentDescription = null)
                        Column {
                            Text("图书榜单", style = MaterialTheme.typography.titleSmall)
                            Text(
                                "畅销 / 热销",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.outline
                            )
                        }
                    }
                }
            }

            Spacer(Modifier.height(8.dp))

            Box(Modifier.fillMaxSize()) {
                when {
                    state.isLoading -> LoadingOverlay()
                    state.error != null -> ErrorMessage(state.error!!)
                    state.books.isEmpty() && query.isNotBlank() ->
                        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                            Text("没有找到相关图书", color = MaterialTheme.colorScheme.outline)
                        }
                    state.books.isEmpty() ->
                        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                            Text(
                                "输入关键词搜索，或浏览分区 / 榜单",
                                color = MaterialTheme.colorScheme.outline
                            )
                        }
                    else -> LazyColumn(
                        contentPadding = PaddingValues(12.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        items(state.books, key = { it.isbn }) { book ->
                            Card(
                                modifier = Modifier.fillMaxWidth(),
                                onClick = { onBookClick(book.isbn) }
                            ) {
                                Row(Modifier.padding(12.dp)) {
                                    BookCover(book = book, modifier = Modifier.size(64.dp, 80.dp))
                                    Spacer(Modifier.width(12.dp))
                                    Column(Modifier.weight(1f)) {
                                        Text(book.title, style = MaterialTheme.typography.bodyLarge)
                                        book.authors?.let {
                                            Text(
                                                it.joinToString("、"),
                                                style = MaterialTheme.typography.bodySmall,
                                                color = MaterialTheme.colorScheme.outline
                                            )
                                        }
                                        Text(
                                            "¥${book.price}",
                                            style = MaterialTheme.typography.titleSmall,
                                            color = MaterialTheme.colorScheme.primary
                                        )
                                        Text(
                                            "库存 ${book.stockQty}",
                                            style = MaterialTheme.typography.labelSmall,
                                            color = MaterialTheme.colorScheme.outline
                                        )
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
