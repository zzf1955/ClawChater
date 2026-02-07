package com.recall.mobile.sync

import android.content.Context
import android.util.Log
import com.recall.mobile.data.AppDatabase
import com.recall.mobile.data.AppPreferences
import com.recall.mobile.data.Screenshot
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import java.util.concurrent.TimeUnit

class SyncManager(context: Context) {
    companion object {
        private const val TAG = "RecallSync"
    }

    private val prefs = AppPreferences(context)
    private val database = AppDatabase.getInstance(context)
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    data class SyncResult(
        val total: Int,
        val success: Int,
        val failed: Int
    )

    suspend fun syncAll(): SyncResult = withContext(Dispatchers.IO) {
        val pending = database.screenshotDao().getPendingSync()
        var success = 0
        var failed = 0

        for (screenshot in pending) {
            if (uploadAndDelete(screenshot)) {
                success++
            } else {
                failed++
            }
        }

        SyncResult(pending.size, success, failed)
    }

    private suspend fun uploadAndDelete(screenshot: Screenshot): Boolean {
        val file = File(screenshot.path)
        if (!file.exists()) {
            // File already deleted, mark as synced
            database.screenshotDao().updateSyncStatus(screenshot.id, "synced")
            return true
        }

        val url = "http://${prefs.serverIp}:${prefs.serverPort}/api/upload"

        try {
            val requestBody = MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart(
                    "file",
                    file.name,
                    file.asRequestBody("image/jpeg".toMediaType())
                )
                .addFormDataPart("timestamp", screenshot.timestamp.toString())
                .build()

            val request = Request.Builder()
                .url(url)
                .post(requestBody)
                .build()

            val response = client.newCall(request).execute()

            if (response.isSuccessful) {
                // Delete local file
                file.delete()
                // Update database status
                database.screenshotDao().updateSyncStatus(screenshot.id, "synced")
                Log.i(TAG, "Synced: ${screenshot.path}")
                return true
            } else {
                Log.e(TAG, "Upload failed: ${response.code} - ${response.message}")
                database.screenshotDao().updateSyncStatus(screenshot.id, "error")
                return false
            }
        } catch (e: Exception) {
            Log.e(TAG, "Sync error: ${screenshot.path}", e)
            database.screenshotDao().updateSyncStatus(screenshot.id, "error")
            return false
        }
    }
}
