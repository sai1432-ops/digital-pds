package com.SIMATS.digitalpds

import android.widget.Toast
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.SIMATS.digitalpds.network.ClinicRequest
import com.SIMATS.digitalpds.network.RetrofitClient
import com.SIMATS.digitalpds.ui.theme.BackgroundWhite
import com.SIMATS.digitalpds.ui.theme.DigitalpdsTheme
import com.SIMATS.digitalpds.ui.theme.PrimaryBlue
import kotlinx.coroutines.launch
import org.json.JSONObject

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AdminAddClinicScreen(
    onBackClick: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    var clinicName by remember { mutableStateOf("") }
    var address by remember { mutableStateOf("") }
    var district by remember { mutableStateOf("") }
    var contactNumber by remember { mutableStateOf("") }
    var website by remember { mutableStateOf("") }
    var isSubmitting by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Add Dental Clinic", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = BackgroundWhite)
            )
        },
        containerColor = BackgroundWhite
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(24.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text("Enter clinic details for users to consult.", color = Color.Gray)

            OutlinedTextField(
                value = clinicName,
                onValueChange = { clinicName = it },
                label = { Text("Clinic Name") },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
            )

            OutlinedTextField(
                value = address,
                onValueChange = { address = it },
                label = { Text("Address") },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                minLines = 2
            )

            OutlinedTextField(
                value = district,
                onValueChange = { district = it },
                label = { Text("District") },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
            )

            OutlinedTextField(
                value = contactNumber,
                onValueChange = { contactNumber = it },
                label = { Text("Contact Number") },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
            )

            OutlinedTextField(
                value = website,
                onValueChange = { website = it },
                label = { Text("Website URL (Optional)") },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                placeholder = { Text("https://example.com") }
            )

            Spacer(modifier = Modifier.height(24.dp))

            Button(
                onClick = {
                    if (clinicName.isBlank() || address.isBlank() || district.isBlank() || contactNumber.isBlank()) {
                        Toast.makeText(context, "Please fill all required fields", Toast.LENGTH_SHORT).show()
                        return@Button
                    }

                    isSubmitting = true
                    scope.launch {
                        try {
                            // Using the existing addClinic endpoint from ApiService
                            // ClinicRequest(clinicName, address, district, contactNumber, latitude, longitude, bookingAvailable)
                            val request = ClinicRequest(
                                clinicName = clinicName,
                                address = address,
                                district = district,
                                contactNumber = contactNumber,
                                bookingAvailable = true
                                // website can be sent in a Map if the backend supports it, 
                                // but for now we follow the existing data class
                            )
                            
                            // If backend supports website, we might need to update ClinicRequest or send as Map
                            // Let's try sending as Map to include website if ApiService allows or if we can change it
                            val response = RetrofitClient.apiService.addClinic(request)
                            
                            if (response.isSuccessful) {
                                Toast.makeText(context, "Clinic added successfully!", Toast.LENGTH_SHORT).show()
                                onBackClick()
                            } else {
                                val errorBody = response.errorBody()?.string()
                                val errorMsg = try {
                                    JSONObject(errorBody ?: "{}").optString("error", "Failed to add clinic")
                                } catch (e: Exception) {
                                    "Failed to add clinic"
                                }
                                Toast.makeText(context, errorMsg, Toast.LENGTH_LONG).show()
                            }
                        } catch (e: Exception) {
                            Toast.makeText(context, "Error: ${e.message}", Toast.LENGTH_SHORT).show()
                        } finally {
                            isSubmitting = false
                        }
                    }
                },
                modifier = Modifier.fillMaxWidth().height(54.dp),
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue),
                enabled = !isSubmitting
            ) {
                if (isSubmitting) CircularProgressIndicator(color = Color.White, modifier = Modifier.size(24.dp))
                else Text("Add Clinic", fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
fun AdminAddClinicScreenPreview() {
    DigitalpdsTheme {
        AdminAddClinicScreen(onBackClick = {})
    }
}
