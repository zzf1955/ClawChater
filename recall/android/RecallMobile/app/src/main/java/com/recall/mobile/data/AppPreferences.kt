package com.recall.mobile.data

import android.content.Context
import android.content.SharedPreferences

class AppPreferences(context: Context) {

    private val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    var captureInterval: Int
        get() = prefs.getInt(KEY_CAPTURE_INTERVAL, DEFAULT_CAPTURE_INTERVAL)
        set(value) = prefs.edit().putInt(KEY_CAPTURE_INTERVAL, value).apply()

    var changeThreshold: Float
        get() = prefs.getFloat(KEY_CHANGE_THRESHOLD, DEFAULT_CHANGE_THRESHOLD)
        set(value) = prefs.edit().putFloat(KEY_CHANGE_THRESHOLD, value).apply()

    var forceInterval: Int
        get() = prefs.getInt(KEY_FORCE_INTERVAL, DEFAULT_FORCE_INTERVAL)
        set(value) = prefs.edit().putInt(KEY_FORCE_INTERVAL, value).apply()

    var screenshotCount: Int
        get() = prefs.getInt(KEY_SCREENSHOT_COUNT, 0)
        set(value) = prefs.edit().putInt(KEY_SCREENSHOT_COUNT, value).apply()

    var isServiceRunning: Boolean
        get() = prefs.getBoolean(KEY_SERVICE_RUNNING, false)
        set(value) = prefs.edit().putBoolean(KEY_SERVICE_RUNNING, value).apply()

    var serverIp: String
        get() = prefs.getString(KEY_SERVER_IP, DEFAULT_SERVER_IP) ?: DEFAULT_SERVER_IP
        set(value) = prefs.edit().putString(KEY_SERVER_IP, value).apply()

    var serverPort: Int
        get() = prefs.getInt(KEY_SERVER_PORT, DEFAULT_SERVER_PORT)
        set(value) = prefs.edit().putInt(KEY_SERVER_PORT, value).apply()

    companion object {
        private const val PREFS_NAME = "recall_prefs"
        private const val KEY_CAPTURE_INTERVAL = "capture_interval"
        private const val KEY_CHANGE_THRESHOLD = "change_threshold"
        private const val KEY_FORCE_INTERVAL = "force_interval"
        private const val KEY_SCREENSHOT_COUNT = "screenshot_count"
        private const val KEY_SERVICE_RUNNING = "service_running"
        private const val KEY_SERVER_IP = "server_ip"
        private const val KEY_SERVER_PORT = "server_port"

        const val DEFAULT_CAPTURE_INTERVAL = 30  // 秒
        const val DEFAULT_CHANGE_THRESHOLD = 0.05f  // 5%
        const val DEFAULT_FORCE_INTERVAL = 300  // 秒
        const val DEFAULT_SERVER_IP = "192.168.1.100"
        const val DEFAULT_SERVER_PORT = 5000
    }
}
