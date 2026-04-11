package com.SIMATS.digitalpds

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.SIMATS.digitalpds.network.Location
import com.SIMATS.digitalpds.network.RetrofitClient
import com.SIMATS.digitalpds.network.SelectLocationRequest
import com.SIMATS.digitalpds.ui.theme.BackgroundWhite
import com.SIMATS.digitalpds.ui.theme.PrimaryBlue
import com.SIMATS.digitalpds.ui.theme.TextBlack
import com.SIMATS.digitalpds.ui.theme.TextGray
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SelectLocationScreen(
    userId: Int,
    onBackClick: () -> Unit,
    onLocationSelected: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    var locations by remember { mutableStateOf<List<Location>>(emptyList()) }
    var selectedLocation by remember { mutableStateOf<Location?>(null) }
    var isLoading by remember { mutableStateOf(true) }
    var isSubmitting by remember { mutableStateOf(false) }

    // Load locations
    LaunchedEffect(Unit) {
        try {
            val response = RetrofitClient.apiService.getLocations()
            if (response.isSuccessful) {
                locations = response.body() ?: emptyList()
            } else {
                Toast.makeText(context, "Failed to load locations", Toast.LENGTH_SHORT).show()
            }
        } catch (e: Exception) {
            Toast.makeText(context, "Error: ${e.message}", Toast.LENGTH_SHORT).show()
        } finally {
            isLoading = false
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Select Your Location", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = BackgroundWhite)
            )
        },
        containerColor = BackgroundWhite
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(24.dp)
        ) {
            Text(
                "Choose your nearest PDS outlet location to assign a dealer.",
                color = TextGray,
                fontSize = 16.sp
            )

            Spacer(modifier = Modifier.height(24.dp))

            if (isLoading) {
                Box(modifier = Modifier.weight(1f).fillMaxWidth(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(color = PrimaryBlue)
                }
            } else {
                LazyColumn(modifier = Modifier.weight(1f)) {
                    items(locations) { loc ->
                        LocationItem(
                            location = loc,
                            isSelected = selectedLocation?.id == loc.id,
                            onClick = { selectedLocation = loc }
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            Button(
                onClick = {
                    if (selectedLocation == null) {
                        Toast.makeText(context, "Please select a location", Toast.LENGTH_SHORT).show()
                        return@Button
                    }

                    isSubmitting = true
                    scope.launch {
                        try {
                            val response = RetrofitClient.apiService.selectLocation(
                                SelectLocationRequest(userId, selectedLocation!!.id)
                            )

                            if (response.isSuccessful) {
                                Toast.makeText(context, "Dealer assigned successfully", Toast.LENGTH_SHORT).show()
                                onLocationSelected()
                            } else {
                                Toast.makeText(context, "Assignment failed", Toast.LENGTH_SHORT).show()
                            }
                        } catch (e: Exception) {
                            Toast.makeText(context, "Error: ${e.message}", Toast.LENGTH_SHORT).show()
                        } finally {
                            isSubmitting = false
                        }
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(54.dp),
                shape = RoundedCornerShape(10.dp),
                enabled = !isSubmitting && selectedLocation != null,
                colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue)
            ) {
                if (isSubmitting) {
                    CircularProgressIndicator(color = Color.White, modifier = Modifier.size(24.dp))
                } else {
                    Text("Confirm Selection", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                }
            }
        }
    }
}

@Composable
fun LocationItem(
    location: Location,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(12.dp),
        color = if (isSelected) PrimaryBlue.copy(alpha = 0.1f) else Color(0xFFF5F7FA),
        border = if (isSelected) androidx.compose.foundation.BorderStroke(2.dp, PrimaryBlue) else null
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                Icons.Default.LocationOn,
                contentDescription = null,
                tint = if (isSelected) PrimaryBlue else TextGray
            )
            Spacer(modifier = Modifier.width(16.dp))
            Column {
                Text(
                    text = location.locationName,
                    fontWeight = FontWeight.Bold,
                    color = if (isSelected) PrimaryBlue else TextBlack,
                    fontSize = 16.sp
                )
                Text(
                    text = "Dealer: ${location.dealerName}",
                    color = TextGray,
                    fontSize = 14.sp
                )
            }
        }
    }
}
