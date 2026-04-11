package com.SIMATS.digitalpds

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Brush
import androidx.compose.material.icons.filled.CleanHands
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Inventory2
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.SIMATS.digitalpds.ui.theme.TextBlack
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DealerStockListScreen(
    itemCounts: List<com.SIMATS.digitalpds.network.ItemCount>,
    onBackClick: () -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Stock Inventory", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.White)
            )
        },
        containerColor = Color(0xFFF8FBFF)
    ) { paddingValues ->
        val groupedDisplayItems = itemCounts
            .map { it.name to (it.count.toIntOrNull() ?: 0) }
            .groupBy { getItemDetails(it.first).name }
            .mapValues { entry -> entry.value.sumOf { it.second } }
            .filter { it.value > 0 }

        if (groupedDisplayItems.isEmpty()) {
            Box(modifier = Modifier.fillMaxSize().padding(paddingValues), contentAlignment = Alignment.Center) {
                Text("No stock items available.", color = Color.Gray)
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(horizontal = 24.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(vertical = 16.dp)
            ) {
                items(groupedDisplayItems.toList()) { (displayName, totalCount) ->
                    val details = getItemDetails(displayName)
                    StockItemRow(details.name, "$totalCount Units", details.icon, details.color)
                }
            }
        }
    }
}

@Composable
private fun StockItemRow(name: String, count: String, icon: ImageVector, iconBg: Color) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Row(
                modifier = Modifier.weight(1f),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(48.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(iconBg),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(icon, contentDescription = null, modifier = Modifier.size(24.dp), tint = Color.DarkGray)
                }
                Spacer(modifier = Modifier.width(16.dp))
                Text(name, fontSize = 16.sp, color = TextBlack, fontWeight = FontWeight.Medium)
            }
            Text(count, fontSize = 16.sp, fontWeight = FontWeight.Bold, color = TextBlack)
        }
    }
}

private data class ItemDetails(val name: String, val icon: ImageVector, val color: Color)

private fun getItemDetails(name: String): ItemDetails {
    val upperName = name.trim().uppercase(Locale.ROOT)
    return when {
        upperName.contains("BRUSH") ->
            ItemDetails("BRUSH", Icons.Default.Brush, Color(0xFFE3F2FD))
            
        upperName == "TOOTHPASTE" || upperName == "PASTE" -> 
            ItemDetails("TOOTHPASTE", Icons.Default.CleanHands, Color(0xFFFFF3E0))
            
        upperName == "FLYER" || upperName == "IEC" || upperName == "FLYERS" -> 
            ItemDetails("FLYER", Icons.Default.Description, Color(0xFFF3E5F5))

        upperName.isBlank() ->
            ItemDetails("UNKNOWN ITEM", Icons.Default.Inventory2, Color(0xFFF5F5F5))
            
        else -> 
            ItemDetails(upperName.replace("_", " "), Icons.Default.Inventory2, Color(0xFFF5F5F5))
    }
}
