package com.recall.mobile

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Bundle
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.recall.mobile.data.AppPreferences
import com.recall.mobile.databinding.ActivityMainBinding
import com.recall.mobile.service.CaptureService
import com.recall.mobile.sync.SyncManager
import com.google.android.material.snackbar.Snackbar
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var prefs: AppPreferences
    private lateinit var projectionManager: MediaProjectionManager

    private val mediaProjectionLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK && result.data != null) {
            CaptureService.startService(this, result.resultCode, result.data!!)
            updateUI(true)
        }
    }

    private val notificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) {
            requestMediaProjection()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        prefs = AppPreferences(this)
        projectionManager = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager

        setupUI()
        updateUI(prefs.isServiceRunning)
    }

    override fun onResume() {
        super.onResume()
        updateUI(prefs.isServiceRunning)
        updateScreenshotCount()
    }

    private fun setupUI() {
        binding.toggleButton.setOnClickListener {
            if (prefs.isServiceRunning) {
                stopCapture()
            } else {
                startCapture()
            }
        }

        binding.settingsButton.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }

        binding.galleryButton.setOnClickListener {
            startActivity(Intent(this, GalleryActivity::class.java))
        }

        binding.syncButton.setOnClickListener {
            syncToPC()
        }
    }

    private fun syncToPC() {
        binding.syncButton.isEnabled = false
        binding.syncButton.text = getString(R.string.syncing)

        CoroutineScope(Dispatchers.Main).launch {
            try {
                val syncManager = SyncManager(this@MainActivity)
                val result = syncManager.syncAll()

                val message = getString(R.string.sync_result, result.success, result.failed)
                Snackbar.make(binding.root, message, Snackbar.LENGTH_LONG).show()
            } catch (e: Exception) {
                Snackbar.make(binding.root, getString(R.string.sync_error), Snackbar.LENGTH_LONG).show()
            } finally {
                binding.syncButton.isEnabled = true
                binding.syncButton.text = getString(R.string.sync_to_pc)
            }
        }
    }

    private fun startCapture() {
        // Android 13+ 需要通知权限
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) {
                notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                return
            }
        }
        requestMediaProjection()
    }

    private fun requestMediaProjection() {
        val intent = projectionManager.createScreenCaptureIntent()
        mediaProjectionLauncher.launch(intent)
    }

    private fun stopCapture() {
        CaptureService.stopService(this)
        updateUI(false)
    }

    private fun updateUI(isRunning: Boolean) {
        if (isRunning) {
            binding.statusIndicator.setBackgroundResource(R.drawable.circle_indicator_active)
            binding.statusText.text = getString(R.string.capture_running)
            binding.toggleButton.text = getString(R.string.stop_capture)
        } else {
            binding.statusIndicator.setBackgroundResource(R.drawable.circle_indicator)
            binding.statusText.text = getString(R.string.capture_stopped)
            binding.toggleButton.text = getString(R.string.start_capture)
        }
    }

    private fun updateScreenshotCount() {
        binding.screenshotCount.text = getString(R.string.screenshot_count, prefs.screenshotCount)
    }
}
