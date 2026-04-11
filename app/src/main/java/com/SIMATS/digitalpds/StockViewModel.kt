package com.SIMATS.digitalpds

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.SIMATS.digitalpds.network.DispatchStockRequestBody
import com.SIMATS.digitalpds.network.RejectStockRequestBody
import com.SIMATS.digitalpds.network.RetrofitClient
import kotlinx.coroutines.launch

enum class StockRequestStatus {
    PENDING, APPROVED, DISPATCHED, REJECTED
}

data class AdminStockRequest(
    val id: Int,
    val itemIds: List<Int>,
    val requestId: String,
    val dealerId: String,
    val dealerName: String,
    val location: String,
    val kitType: String,
    val quantity: String,
    val status: StockRequestStatus,
    val requestDate: String,
    val approvedAt: String? = null,
    val rejectedAt: String? = null,
    val dispatchedAt: String? = null,
    val adminNote: String? = null,
    val courierName: String? = null,
    val trackingId: String? = null,
    val dealerAddress: String? = null,
    val dealerUsername: String? = null,
    val dispatchAddress: String? = null,
    val dispatchUsername: String? = null
)

class StockViewModel : ViewModel() {
    var requests by mutableStateOf<List<AdminStockRequest>>(emptyList())
    var isLoading by mutableStateOf(false)
    var message by mutableStateOf<String?>(null)

    fun fetchRequests() {
        viewModelScope.launch {
            isLoading = true
            try {
                val response = RetrofitClient.apiService.getAdminStockRequests()
                if (response.isSuccessful) {
                    val rawList = response.body() ?: emptyList()
                    val grouped = rawList.groupBy { it.requestId }
                    
                    requests = grouped.map { (gid, dtos) ->
                        val first = dtos.first()
                        val itemsSummary = dtos.joinToString(", ") {
                            "${it.kitType.ifBlank { "Unknown Item" }} (${it.quantity})"
                        }
                        
                        AdminStockRequest(
                            id = first.id,
                            itemIds = dtos.map { it.id },
                            requestId = gid,
                            dealerId = first.dealerId.toString(),
                            dealerName = first.dealerName,
                            location = first.location,
                            kitType = itemsSummary,
                            quantity = "${dtos.size} Item Types",
                            status = when (first.status.uppercase()) {
                                "APPROVED" -> StockRequestStatus.APPROVED
                                "DISPATCHED" -> StockRequestStatus.DISPATCHED
                                "REJECTED" -> StockRequestStatus.REJECTED
                                else -> StockRequestStatus.PENDING
                            },
                            requestDate = first.requestDate,
                            approvedAt = first.approvedAt,
                            rejectedAt = first.rejectedAt,
                            dispatchedAt = first.dispatchedAt,
                            adminNote = first.adminNote,
                            courierName = first.courierName,
                            trackingId = first.trackingId,
                            dealerAddress = first.dealerAddress,
                            dealerUsername = first.dealerUsername,
                            dispatchAddress = first.dispatchAddress,
                            dispatchUsername = first.dispatchUsername
                        )
                    }.sortedByDescending { it.requestDate }
                } else {
                    message = "Failed to load stock requests"
                }
            } catch (e: Exception) {
                message = e.message ?: "Something went wrong"
            } finally {
                isLoading = false
            }
        }
    }

    fun approveRequest(group: AdminStockRequest, onDone: () -> Unit = {}) {
        viewModelScope.launch {
            var allSuccess = true
            for (id in group.itemIds) {
                try {
                    val response = RetrofitClient.apiService.approveStockRequest(id)
                    if (!response.isSuccessful) allSuccess = false
                } catch (e: Exception) {
                    allSuccess = false
                }
            }
            
            if (allSuccess) {
                message = "Request group approved"
                fetchRequests()
                onDone()
            } else {
                message = "Failed to approve some items in the request"
            }
        }
    }

    fun dispatchRequest(
        group: AdminStockRequest,
        courierName: String,
        trackingId: String,
        onDone: () -> Unit = {}
    ) {
        viewModelScope.launch {
            var allSuccess = true

            val body = DispatchStockRequestBody(
                courierName = courierName,
                trackingId = trackingId
            )

            for (id in group.itemIds) {
                try {
                    val response = RetrofitClient.apiService.dispatchStockRequest(id, body)
                    if (!response.isSuccessful) allSuccess = false
                } catch (e: Exception) {
                    allSuccess = false
                }
            }

            if (allSuccess) {
                message = "Request group dispatched"
                fetchRequests()
                onDone()
            } else {
                message = "Failed to dispatch some items"
            }
        }
    }

    fun rejectRequest(group: AdminStockRequest, reason: String, onDone: () -> Unit = {}) {
        viewModelScope.launch {
            var allSuccess = true
            for (id in group.itemIds) {
                try {
                    val response = RetrofitClient.apiService.rejectStockRequest(
                        id,
                        RejectStockRequestBody(reason.ifBlank { null })
                    )
                    if (!response.isSuccessful) allSuccess = false
                } catch (e: Exception) {
                    allSuccess = false
                }
            }
            
            if (allSuccess) {
                message = "Request group rejected"
                fetchRequests()
                onDone()
            } else {
                message = "Failed to reject some items"
            }
        }
    }

    fun clearMessage() {
        message = null
    }
}
