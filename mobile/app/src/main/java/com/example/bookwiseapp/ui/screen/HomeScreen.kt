package com.example.bookwiseapp.ui.screen

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.staggeredgrid.LazyVerticalStaggeredGrid
import androidx.compose.foundation.lazy.staggeredgrid.StaggeredGridCells
import androidx.compose.foundation.lazy.staggeredgrid.items
import androidx.compose.foundation.lazy.staggeredgrid.LazyStaggeredGridState
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.example.bookwiseapp.data.api.model.BookData
import com.example.bookwiseapp.ui.component.BookCover
import com.example.bookwiseapp.ui.component.ErrorMessage
import com.example.bookwiseapp.ui.component.LoadingOverlay
import com.example.bookwiseapp.viewmodel.BookViewModel
import com.example.bookwiseapp.viewmodel.CartViewModel
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.filter
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    viewModel: BookViewModel,
    cartVm: CartViewModel,
    onBookClick: (String) -> Unit
) {
    val state by viewModel.homeState.collectAsState()
    val gridState = rememberSaveable(saver = LazyStaggeredGridState.Saver) {
        LazyStaggeredGridState()
    }
    val scope = rememberCoroutineScope()

    fun refreshAndScrollTop() {
        scope.launch {
            gridState.animateScrollToItem(0)
        }
        viewModel.refreshBooks()
    }

    LaunchedEffect(Unit) { viewModel.loadBooks() }

    LaunchedEffect(gridState, state.books.size, state.hasMore) {
        snapshotFlow {
            val info = gridState.layoutInfo
            val lastVisible = info.visibleItemsInfo.lastOrNull()?.index ?: 0
            lastVisible >= info.totalItemsCount - 4 && info.totalItemsCount > 0
        }
            .distinctUntilChanged()
            .filter {
                it && state.hasMore && !state.isLoadingMore && !state.isLoading && !state.isRefreshing
            }
            .collect { viewModel.loadMoreBooks() }
    }

    Scaffold(
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("书城")
                        if (state.isRefreshing) {
                            Text(
                                text = "刷新中...",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.outline
                            )
                        }
                    }
                },
                actions = {
                    IconButton(onClick = { refreshAndScrollTop() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "刷新推荐")
                    }
                }
            )
        }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when {
                state.isLoading && state.books.isEmpty() -> LoadingOverlay()
                state.error != null && state.books.isEmpty() ->
                    ErrorMessage(state.error!!, onRetry = { viewModel.loadBooks() })
                else -> {
                    PullToRefreshBox(
                        isRefreshing = state.isRefreshing,
                        onRefresh = { refreshAndScrollTop() },
                        modifier = Modifier.fillMaxSize()
                    ) {
                        LazyVerticalStaggeredGrid(
                            columns = StaggeredGridCells.Fixed(2),
                            state = gridState,
                            contentPadding = PaddingValues(8.dp),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalItemSpacing = 8.dp,
                            modifier = Modifier.fillMaxSize()
                        ) {
                            items(state.books, key = { it.isbn }) { book ->
                                BookCard(
                                    book = book,
                                    defaultCoverUrl = state.defaultCoverUrl,
                                    onClick = { onBookClick(book.isbn) }
                                )
                            }
                            if (state.isLoadingMore) {
                                item {
                                    Box(
                                        Modifier
                                            .fillMaxWidth()
                                            .padding(16.dp),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        CircularProgressIndicator(Modifier.size(28.dp))
                                    }
                                }
                            }
                            if (!state.hasMore && state.books.isNotEmpty() && !state.isRefreshing) {
                                item {
                                    Box(
                                        Modifier
                                            .fillMaxWidth()
                                            .padding(vertical = 24.dp),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        TextButton(onClick = { refreshAndScrollTop() }) {
                                            Text("换一批看看🔄")
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

@Composable
fun BookCard(
    book: BookData,
    onClick: () -> Unit,
    defaultCoverUrl: String = ""
) {
    Card(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        elevation = CardDefaults.cardElevation(2.dp)
    ) {
        Column {
            BookCover(
                book = book,
                defaultCoverUrl = defaultCoverUrl.ifBlank { null },
                modifier = Modifier.fillMaxWidth().height(160.dp)
            )
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
