package com.example.bookwiseapp.ui.screen

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.staggeredgrid.LazyVerticalStaggeredGrid
import androidx.compose.foundation.lazy.staggeredgrid.StaggeredGridCells
import androidx.compose.foundation.lazy.staggeredgrid.items
import androidx.compose.material3.*
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.example.bookwiseapp.data.api.model.BookData
import com.example.bookwiseapp.ui.component.BookCover
import com.example.bookwiseapp.ui.component.ErrorMessage
import com.example.bookwiseapp.ui.component.LoadingOverlay
import com.example.bookwiseapp.viewmodel.BookViewModel
import com.example.bookwiseapp.viewmodel.CartViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    viewModel: BookViewModel,
    cartVm: CartViewModel,
    onBookClick: (String) -> Unit
) {
    val state by viewModel.homeState.collectAsState()

    LaunchedEffect(Unit) { viewModel.loadBooks() }

    Scaffold(
        topBar = { TopAppBar(title = { Text("书城") }) }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when {
                state.isLoading && state.books.isEmpty() -> LoadingOverlay()
                state.error != null && state.books.isEmpty() ->
                    ErrorMessage(state.error!!, onRetry = { viewModel.loadBooks() })
                else ->
                    // 下拉刷新容器
                    PullToRefreshBox(
                        isRefreshing = state.isLoading,
                        onRefresh = { viewModel.loadBooks() },
                        modifier = Modifier.fillMaxSize()
                    ) {
                        // 瀑布流网格：每列独立高度，卡片紧凑排列无多余空隙
                        LazyVerticalStaggeredGrid(
                            columns = StaggeredGridCells.Fixed(2),
                            contentPadding = PaddingValues(8.dp),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalItemSpacing = 8.dp,
                            modifier = Modifier.fillMaxSize()
                        ) {
                            items(state.books, key = { it.isbn }) { book ->
                                BookCard(book = book, onClick = { onBookClick(book.isbn) })
                            }
                        }
                    }
            }
        }
    }
}

@Composable
fun BookCard(book: BookData, onClick: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        elevation = CardDefaults.cardElevation(2.dp)
    ) {
        Column {
            BookCover(book = book, modifier = Modifier.fillMaxWidth().height(160.dp))
            Column(Modifier.padding(8.dp)) {
                Text(
                    text = book.title,
                    style = MaterialTheme.typography.bodyMedium,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "¥${book.price}",
                    style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.primary
                )
                Text(
                    text = "库存 ${book.stockQty}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.outline
                )
            }
        }
    }
}
