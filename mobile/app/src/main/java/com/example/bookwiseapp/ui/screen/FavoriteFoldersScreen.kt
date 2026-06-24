package com.example.bookwiseapp.ui.screen

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.example.bookwiseapp.ui.component.BookCover
import com.example.bookwiseapp.ui.component.ErrorMessage
import com.example.bookwiseapp.ui.component.LoadingOverlay
import com.example.bookwiseapp.viewmodel.FavoriteViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FavoriteFoldersScreen(
    viewModel: FavoriteViewModel,
    onBookClick: (String) -> Unit,
    onBack: () -> Unit
) {
    val state by viewModel.state.collectAsState()
    var showCreate by remember { mutableStateOf(false) }
    var newFolderName by remember { mutableStateOf("") }
    val snackbarHost = remember { SnackbarHostState() }

    LaunchedEffect(Unit) { viewModel.loadFolders() }
    LaunchedEffect(state.message) {
        state.message?.let {
            snackbarHost.showSnackbar(it)
            viewModel.clearMessage()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("我的收藏 (${state.totalCount})") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "返回")
                    }
                },
                actions = {
                    TextButton(onClick = { showCreate = true }) { Text("新建") }
                }
            )
        },
        snackbarHost = { SnackbarHost(snackbarHost) }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when {
                state.isLoading && state.folders.isEmpty() -> LoadingOverlay()
                state.error != null && state.folders.isEmpty() ->
                    ErrorMessage(state.error!!, onRetry = { viewModel.loadFolders() })
                else -> LazyColumn(
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(state.folders, key = { it.folder.id }) { card ->
                        Card(Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(12.dp)) {
                                Row(
                                    Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Column {
                                        Text(card.folder.name, style = MaterialTheme.typography.titleMedium)
                                        Text(
                                            "${card.count} 本",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.outline
                                        )
                                    }
                                    if (!card.folder.isDefault) {
                                        IconButton(onClick = { viewModel.deleteFolder(card.folder.id) }) {
                                            Icon(
                                                Icons.Default.Delete,
                                                contentDescription = "删除收藏夹",
                                                tint = MaterialTheme.colorScheme.error
                                            )
                                        }
                                    }
                                }
                                Spacer(Modifier.height(8.dp))
                                card.books?.forEach { book ->
                                    Row(
                                        Modifier
                                            .fillMaxWidth()
                                            .clickable { onBookClick(book.isbn) }
                                            .padding(vertical = 6.dp),
                                        horizontalArrangement = Arrangement.spacedBy(10.dp),
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        BookCover(book = book, modifier = Modifier.size(48.dp, 64.dp))
                                        Column(Modifier.weight(1f)) {
                                            Text(
                                                book.title,
                                                maxLines = 2,
                                                overflow = TextOverflow.Ellipsis,
                                                style = MaterialTheme.typography.bodyMedium
                                            )
                                            Text(
                                                "¥${book.price}",
                                                style = MaterialTheme.typography.bodySmall,
                                                color = MaterialTheme.colorScheme.primary
                                            )
                                        }
                                    }
                                }
                                if (card.books.isNullOrEmpty()) {
                                    Text(
                                        "暂无收藏",
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

    if (showCreate) {
        AlertDialog(
            onDismissRequest = { showCreate = false; newFolderName = "" },
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
                        viewModel.createFolder(newFolderName.trim())
                        showCreate = false
                        newFolderName = ""
                    },
                    enabled = newFolderName.isNotBlank()
                ) { Text("创建") }
            },
            dismissButton = {
                TextButton(onClick = { showCreate = false; newFolderName = "" }) { Text("取消") }
            }
        )
    }
}
