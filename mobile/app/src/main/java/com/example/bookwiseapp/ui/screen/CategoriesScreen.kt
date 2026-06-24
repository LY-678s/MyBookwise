package com.example.bookwiseapp.ui.screen

import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.staggeredgrid.LazyVerticalStaggeredGrid
import androidx.compose.foundation.lazy.staggeredgrid.StaggeredGridCells
import androidx.compose.foundation.lazy.staggeredgrid.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.example.bookwiseapp.ui.component.ErrorMessage
import com.example.bookwiseapp.ui.component.LoadingOverlay
import com.example.bookwiseapp.viewmodel.BookViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CategoriesScreen(
    viewModel: BookViewModel,
    onBookClick: (String) -> Unit,
    onBack: () -> Unit
) {
    val state by viewModel.categoriesState.collectAsState()
    var sortExpanded by remember { mutableStateOf(false) }
    val sortOptions = listOf(
        "title" to "书名",
        "price_asc" to "价格升序",
        "price_desc" to "价格降序",
        "stock_desc" to "库存优先"
    )

    LaunchedEffect(Unit) {
        viewModel.loadCategories()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("书籍分区") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "返回")
                    }
                },
                actions = {
                    Box {
                        TextButton(onClick = { sortExpanded = true }) {
                            Text(sortOptions.firstOrNull { it.first == state.sort }?.second ?: "排序")
                        }
                        DropdownMenu(expanded = sortExpanded, onDismissRequest = { sortExpanded = false }) {
                            sortOptions.forEach { (value, label) ->
                                DropdownMenuItem(
                                    text = { Text(label) },
                                    onClick = {
                                        sortExpanded = false
                                        viewModel.loadCategories(state.selectedCategory, value, 1)
                                    }
                                )
                            }
                        }
                    }
                }
            )
        }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when {
                state.isLoading && state.books.isEmpty() && state.categories.isEmpty() -> LoadingOverlay()
                state.error != null && state.books.isEmpty() ->
                    ErrorMessage(state.error!!, onRetry = { viewModel.loadCategories() })
                else -> Column(Modifier.fillMaxSize()) {
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .horizontalScroll(rememberScrollState())
                            .padding(horizontal = 8.dp, vertical = 8.dp),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        FilterChip(
                            selected = state.selectedCategory.isBlank(),
                            onClick = { viewModel.loadCategories("", state.sort, 1) },
                            label = { Text("全部") }
                        )
                        state.categories.forEach { category ->
                            FilterChip(
                                selected = state.selectedCategory == category.name,
                                onClick = {
                                    viewModel.loadCategories(category.name, state.sort, 1)
                                },
                                label = { Text("${category.name} (${category.count})") }
                            )
                        }
                    }

                    LazyVerticalStaggeredGrid(
                        columns = StaggeredGridCells.Fixed(2),
                        contentPadding = PaddingValues(8.dp),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalItemSpacing = 8.dp,
                        modifier = Modifier.weight(1f)
                    ) {
                        items(state.books, key = { it.isbn }) { book ->
                            BookCard(book = book, onClick = { onBookClick(book.isbn) })
                        }
                    }

                    if (state.totalPages > 1) {
                        Row(
                            Modifier
                                .fillMaxWidth()
                                .padding(8.dp),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            TextButton(
                                onClick = {
                                    if (state.currentPage > 1) {
                                        viewModel.loadCategories(
                                            state.selectedCategory,
                                            state.sort,
                                            state.currentPage - 1
                                        )
                                    }
                                },
                                enabled = state.currentPage > 1 && !state.isLoading
                            ) { Text("上一页") }
                            Text(
                                "${state.currentPage}/${state.totalPages}",
                                style = MaterialTheme.typography.bodyMedium,
                                modifier = Modifier.align(androidx.compose.ui.Alignment.CenterVertically)
                            )
                            TextButton(
                                onClick = {
                                    if (state.currentPage < state.totalPages) {
                                        viewModel.loadCategories(
                                            state.selectedCategory,
                                            state.sort,
                                            state.currentPage + 1
                                        )
                                    }
                                },
                                enabled = state.currentPage < state.totalPages && !state.isLoading
                            ) { Text("下一页") }
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RankingsScreen(
    viewModel: BookViewModel,
    onBookClick: (String) -> Unit,
    onBack: () -> Unit
) {
    val state by viewModel.rankingsState.collectAsState()

    LaunchedEffect(Unit) { viewModel.loadRankings() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("图书榜单") },
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
                state.isLoading && state.sections.isEmpty() -> LoadingOverlay()
                state.error != null && state.sections.isEmpty() ->
                    ErrorMessage(state.error!!, onRetry = { viewModel.loadRankings() })
                else -> androidx.compose.foundation.lazy.LazyColumn(
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    state.sections.forEach { section ->
                        item(key = section.title) {
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Text(section.title, style = MaterialTheme.typography.titleLarge)
                                Text(
                                    section.subtitle,
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.outline
                                )
                                section.books?.forEachIndexed { index, book ->
                                    Card(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .clickable { onBookClick(book.isbn) }
                                    ) {
                                        Row(
                                            Modifier.padding(12.dp),
                                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                                        ) {
                                            Text(
                                                "${index + 1}",
                                                style = MaterialTheme.typography.titleMedium,
                                                color = MaterialTheme.colorScheme.primary,
                                                modifier = Modifier.width(28.dp)
                                            )
                                            Column(Modifier.weight(1f)) {
                                                Text(
                                                    book.title,
                                                    style = MaterialTheme.typography.bodyLarge,
                                                    maxLines = 2,
                                                    overflow = TextOverflow.Ellipsis
                                                )
                                                Text(
                                                    "¥${book.price}",
                                                    style = MaterialTheme.typography.bodyMedium,
                                                    color = MaterialTheme.colorScheme.primary
                                                )
                                                book.metricLabel?.let { label ->
                                                    Text(
                                                        "$label: ${book.metricValue ?: 0}",
                                                        style = MaterialTheme.typography.bodySmall,
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
        }
    }
}
