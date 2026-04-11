package com.SIMATS.digitalpds.notification

import android.content.Context
import android.content.SharedPreferences
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

object CheckInPrefs {
    private const val PREFS_NAME = "check_in_prefs"
    private const val KEY_LAST_RESET_DATE = "last_reset_date"
    private const val KEY_MORNING_CHECKED_IN = "morning_checked_in"
    private const val KEY_EVENING_CHECKED_IN = "evening_checked_in"

    private fun getPrefs(context: Context): SharedPreferences {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    fun isMorningCheckedIn(context: Context): Boolean {
        resetIfNewDay(context)
        return getPrefs(context).getBoolean(KEY_MORNING_CHECKED_IN, false)
    }

    fun setMorningCheckedIn(context: Context, checkedIn: Boolean) {
        getPrefs(context).edit().putBoolean(KEY_MORNING_CHECKED_IN, checkedIn).apply()
    }

    fun isEveningCheckedIn(context: Context): Boolean {
        resetIfNewDay(context)
        return getPrefs(context).getBoolean(KEY_EVENING_CHECKED_IN, false)
    }

    fun setEveningCheckedIn(context: Context, checkedIn: Boolean) {
        getPrefs(context).edit().putBoolean(KEY_EVENING_CHECKED_IN, checkedIn).apply()
    }

    fun resetIfNewDay(context: Context) {
        val prefs = getPrefs(context)
        val lastResetDate = prefs.getString(KEY_LAST_RESET_DATE, "")
        val currentDate = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date())

        if (lastResetDate != currentDate) {
            prefs.edit()
                .putString(KEY_LAST_RESET_DATE, currentDate)
                .putBoolean(KEY_MORNING_CHECKED_IN, false)
                .putBoolean(KEY_EVENING_CHECKED_IN, false)
                .apply()
        }
    }
}
