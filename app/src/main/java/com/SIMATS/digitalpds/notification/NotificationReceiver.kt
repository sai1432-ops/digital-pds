package com.SIMATS.digitalpds.notification

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

class NotificationReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val type = intent.getStringExtra("type") ?: return
        
        when (type) {
            "MORNING_REMINDER" -> {
                if (!CheckInPrefs.isMorningCheckedIn(context)) {
                    NotificationHelper.showNotification(
                        context,
                        1,
                        "Morning Brushing Reminder",
                        "Good morning! Please brush your teeth and complete your morning check-in."
                    )
                }
            }
            "MORNING_MISSED" -> {
                if (!CheckInPrefs.isMorningCheckedIn(context)) {
                    NotificationHelper.showNotification(
                        context,
                        2,
                        "Morning Check-in Missed",
                        "You missed your morning brushing check-in today. Please try to maintain your oral care routine."
                    )
                }
            }
            "EVENING_REMINDER" -> {
                if (!CheckInPrefs.isEveningCheckedIn(context)) {
                    NotificationHelper.showNotification(
                        context,
                        3,
                        "Evening Brushing Reminder",
                        "It is time for your evening brushing. Please brush your teeth and complete your evening check-in."
                    )
                }
            }
            "EVENING_MISSED" -> {
                if (!CheckInPrefs.isEveningCheckedIn(context)) {
                    NotificationHelper.showNotification(
                        context,
                        4,
                        "Evening Check-in Missed",
                        "You missed your evening brushing check-in today. Stay consistent for better dental health."
                    )
                }
            }
        }
    }
}
