package com.recall.mobile.capture

import android.graphics.Bitmap
import android.graphics.Color
import kotlin.math.abs

/**
 * 屏幕变化检测器
 * 通过对比缩略图像素差异来判断屏幕是否发生变化
 */
class ChangeDetector {
    private var lastThumbnail: Bitmap? = null
    private var lastCaptureTime: Long = 0

    /**
     * 检测是否应该保存截图
     * @param thumbnail 当前截图的缩略图
     * @param threshold 变化阈值 (0-1)
     * @param forceInterval 强制截图间隔（毫秒）
     * @return true 表示应该保存
     */
    fun shouldCapture(thumbnail: Bitmap, threshold: Float, forceInterval: Long): Boolean {
        val now = System.currentTimeMillis()

        // 首次截图
        if (lastThumbnail == null) {
            lastThumbnail = thumbnail.copy(Bitmap.Config.ARGB_8888, false)
            lastCaptureTime = now
            return true
        }

        // 强制截图间隔
        if (now - lastCaptureTime >= forceInterval) {
            lastThumbnail = thumbnail.copy(Bitmap.Config.ARGB_8888, false)
            lastCaptureTime = now
            return true
        }

        // 计算变化率
        val changeRatio = calculateChangeRatio(lastThumbnail!!, thumbnail)
        if (changeRatio >= threshold) {
            lastThumbnail = thumbnail.copy(Bitmap.Config.ARGB_8888, false)
            lastCaptureTime = now
            return true
        }

        return false
    }

    /**
     * 计算两张图片的像素变化比例
     */
    private fun calculateChangeRatio(old: Bitmap, new: Bitmap): Float {
        if (old.width != new.width || old.height != new.height) {
            return 1f  // 尺寸不同，视为完全变化
        }

        val width = old.width
        val height = old.height
        var changedPixels = 0
        val totalPixels = width * height
        val pixelThreshold = 30  // 单像素差异阈值

        for (y in 0 until height) {
            for (x in 0 until width) {
                val oldPixel = old.getPixel(x, y)
                val newPixel = new.getPixel(x, y)

                val rDiff = abs(Color.red(oldPixel) - Color.red(newPixel))
                val gDiff = abs(Color.green(oldPixel) - Color.green(newPixel))
                val bDiff = abs(Color.blue(oldPixel) - Color.blue(newPixel))

                if (rDiff > pixelThreshold || gDiff > pixelThreshold || bDiff > pixelThreshold) {
                    changedPixels++
                }
            }
        }

        return changedPixels.toFloat() / totalPixels
    }

    fun reset() {
        lastThumbnail?.recycle()
        lastThumbnail = null
        lastCaptureTime = 0
    }
}
