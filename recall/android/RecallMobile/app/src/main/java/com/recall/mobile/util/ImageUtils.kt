package com.recall.mobile.util

import android.graphics.Bitmap
import android.os.Environment
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.*

object ImageUtils {
    private const val TAG = "RecallMobile"
    private const val JPEG_QUALITY = 85
    private const val THUMBNAIL_SIZE = 200

    /**
     * 保存截图到 Pictures/Recall/YYYY-MM-DD/HH/HHMMSS.jpg
     */
    fun saveScreenshot(bitmap: Bitmap, timestamp: Long): String? {
        val dateFormat = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
        val hourFormat = SimpleDateFormat("HH", Locale.getDefault())
        val fileFormat = SimpleDateFormat("HHmmss", Locale.getDefault())

        val date = Date(timestamp)
        val datePath = dateFormat.format(date)
        val hourPath = hourFormat.format(date)
        val fileName = "${fileFormat.format(date)}.jpg"

        val baseDir = File(
            Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES),
            "Recall"
        )
        val dir = File(baseDir, "$datePath/$hourPath")

        if (!dir.exists() && !dir.mkdirs()) {
            return null
        }

        val file = File(dir, fileName)
        return try {
            FileOutputStream(file).use { out ->
                bitmap.compress(Bitmap.CompressFormat.JPEG, JPEG_QUALITY, out)
            }
            file.absolutePath
        } catch (e: Exception) {
            android.util.Log.e(TAG, "Failed to save screenshot", e)
            null
        }
    }

    /**
     * 创建缩略图用于变化检测
     */
    fun createThumbnail(bitmap: Bitmap): Bitmap {
        return Bitmap.createScaledBitmap(bitmap, THUMBNAIL_SIZE, THUMBNAIL_SIZE, true)
    }
}
