package com.example.bookwiseapp.ui.screen

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.example.bookwiseapp.ui.component.BookCover
import com.example.bookwiseapp.ui.component.ErrorMessage
import com.example.bookwiseapp.ui.component.LoadingOverlay
import com.example.bookwiseapp.viewmodel.AccountViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BrowseHistoryScreen(
    viewModel: AccountViewModel,
    onBookClick: (String) -> Unit,
    onBack: () -> Unit
) {
    val state by viewModel.browseHistoryState.collectAsState()

    LaunchedEffect(Unit) { viewModel.loadBrowseHistory() }

    Scaffold(
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
        topBar = {
            TopAppBar(
                title = { Text("最近浏览") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "返回")
                    }
                }
            )
        }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when {
                state.isLoading && state.books.isEmpty() -> LoadingOverlay()
                state.error != null && state.books.isEmpty() ->
                    ErrorMessage(state.error!!, onRetry = { viewModel.loadBrowseHistory() })
                state.books.isEmpty() -> Box(Modifier.fillMaxSize(), contentAlignment = androidx.compose.ui.Alignment.Center) {
                    Text("暂无浏览记录", color = MaterialTheme.colorScheme.outline)
                }
                else -> LazyVerticalGrid(
                    columns = GridCells.Fixed(2),
                    contentPadding = PaddingValues(12.dp),
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    items(state.books, key = { it.isbn }) { book ->
                        Card(
                            Modifier.fillMaxWidth().clickable { onBookClick(book.isbn) }
                        ) {
                            Column {
                                BookCover(
                                    book = book,
                                    defaultCoverUrl = state.defaultCoverUrl,
                                    modifier = Modifier.fillMaxWidth().height(160.dp)
                                )
                                Column(Modifier.padding(8.dp)) {
                                    Text(
                                        book.title,
                                        maxLines = 2,
                                        overflow = TextOverflow.Ellipsis,
                                        style = MaterialTheme.typography.bodyMedium
                                    )
                                    Text(
                                        "¥${book.price}",
                                        style = MaterialTheme.typography.labelLarge,
                                        color = MaterialTheme.colorScheme.primary
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
