package com.recall.mobile.capture

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.util.DisplayMetrics
import android.util.Log
import android.view.WindowManager
import com.recall.mobile.data.AppDatabase
import com.recall.mobile.data.AppPreferences
import com.recall.mobile.data.Screenshot
import com.recall.mobile.util.ImageUtils
import kotlinx.coroutines.*

/**
 * 屏幕截图管理器
 */
class ScreenCapture(
    private val context: Context,
    private val resultCode: Int,
    private val data: Intent
) {
    companion object {
        private const val TAG = "RecallMobile"
    }

    private val projectionManager = context.getSystemService(Context.MEDIA_PROJECTION_SERVICE)
            as MediaProjectionManager
    private val windowManager = context.getSystemService(Context.WINDOW_SERVICE)
            as WindowManager
    private val mainHandler = android.os.Handler(android.os.Looper.getMainLooper())

    private var mediaProjection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var imageReader: ImageReader? = null

    private val changeDetector = ChangeDetector()
    private val prefs = AppPreferences(context)
    private val database = AppDatabase.getInstance(context)

    private var captureJob: Job? = null
    private var isRunning = false

    private val screenWidth: Int
    private val screenHeight: Int
    private val screenDensity: Int

    // MediaProjection 回调 (Android 14+ 必需)
    private val projectionCallback = object : MediaProjection.Callback() {
        override fun onStop() {
            Log.i(TAG, "MediaProjection stopped by system")
            stop()
        }
    }

    init {
        val metrics = DisplayMetrics()
        @Suppress("DEPRECATION")
        windowManager.defaultDisplay.getRealMetrics(metrics)
        screenWidth = metrics.widthPixels
        screenHeight = metrics.heightPixels
        screenDensity = metrics.densityDpi
    }

    @SuppressLint("WrongConstant")
    fun start() {
        if (isRunning) return

        try {
            mediaProjection = projectionManager.getMediaProjection(resultCode, data)
            if (mediaProjection == null) {
                Log.e(TAG, "Failed to get MediaProjection")
                return
            }

            // 注册回调 (Android 14+ 必需)
            mediaProjection?.registerCallback(projectionCallback, mainHandler)

            imageReader = ImageReader.newInstance(
                screenWidth, screenHeight,
                PixelFormat.RGBA_8888, 2
            )

            virtualDisplay = mediaProjection?.createVirtualDisplay(
                "RecallCapture",
                screenWidth, screenHeight, screenDensity,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
                imageReader?.surface, null, null
            )

            isRunning = true
            startCaptureLoop()
            Log.i(TAG, "Screen capture started")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start capture", e)
            stop()
        }
    }

    fun stop() {
        isRunning = false
        captureJob?.cancel()
        captureJob = null

        virtualDisplay?.release()
        virtualDisplay = null

        imageReader?.close()
        imageReader = null

        try {
            mediaProjection?.unregisterCallback(projectionCallback)
        } catch (e: Exception) {
            // 忽略
        }
        mediaProjection?.stop()
        mediaProjection = null

        changeDetector.reset()
        Log.i(TAG, "Screen capture stopped")
    }

    private fun startCaptureLoop() {
        captureJob = CoroutineScope(Dispatchers.IO).launch {
            while (isRunning) {
                try {
                    captureScreen()
                } catch (e: Exception) {
                    Log.e(TAG, "Capture error", e)
                }
                delay(prefs.captureInterval * 1000L)
            }
        }
    }

    private suspend fun captureScreen() {
        val image = imageReader?.acquireLatestImage() ?: return

        try {
            val planes = image.planes
            val buffer = planes[0].buffer
            val pixelStride = planes[0].pixelStride
            val rowStride = planes[0].rowStride
            val rowPadding = rowStride - pixelStride * screenWidth

            val bitmap = Bitmap.createBitmap(
                screenWidth + rowPadding / pixelStride,
                screenHeight,
                Bitmap.Config.ARGB_8888
            )
            bitmap.copyPixelsFromBuffer(buffer)

            // 裁剪到实际屏幕尺寸
            val croppedBitmap = Bitmap.createBitmap(bitmap, 0, 0, screenWidth, screenHeight)
            bitmap.recycle()

            // 创建缩略图进行变化检测
            val thumbnail = ImageUtils.createThumbnail(croppedBitmap)
            val forceIntervalMs = prefs.forceInterval * 1000L

            if (changeDetector.shouldCapture(thumbnail, prefs.changeThreshold, forceIntervalMs)) {
                val timestamp = System.currentTimeMillis()
                val path = ImageUtils.saveScreenshot(croppedBitmap, timestamp)

                if (path != null) {
                    // 保存到数据库
                    database.screenshotDao().insert(
                        Screenshot(path = path, timestamp = timestamp)
                    )
                    prefs.screenshotCount = prefs.screenshotCount + 1
                    Log.i(TAG, "Screenshot saved: $path")
                }
            }

            thumbnail.recycle()
            croppedBitmap.recycle()
        } finally {
            image.close()
        }
    }
}
