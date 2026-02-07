package com.recall.mobile

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.recall.mobile.data.AppPreferences
import com.recall.mobile.databinding.ActivitySettingsBinding

class SettingsActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySettingsBinding
    private lateinit var prefs: AppPreferences

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySettingsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = getString(R.string.settings)

        prefs = AppPreferences(this)
        setupSliders()
    }

    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }

    private fun setupSliders() {
        // 截图间隔
        binding.intervalSlider.value = prefs.captureInterval.toFloat()
        binding.intervalValue.text = "${prefs.captureInterval} 秒"
        binding.intervalSlider.addOnChangeListener { _, value, _ ->
            prefs.captureInterval = value.toInt()
            binding.intervalValue.text = "${value.toInt()} 秒"
        }

        // 变化阈值
        val thresholdPercent = (prefs.changeThreshold * 100).toInt()
        binding.thresholdSlider.value = thresholdPercent.toFloat()
        binding.thresholdValue.text = "$thresholdPercent%"
        binding.thresholdSlider.addOnChangeListener { _, value, _ ->
            prefs.changeThreshold = value / 100f
            binding.thresholdValue.text = "${value.toInt()}%"
        }

        // 强制截图间隔
        binding.forceIntervalSlider.value = prefs.forceInterval.toFloat()
        binding.forceIntervalValue.text = "${prefs.forceInterval} 秒"
        binding.forceIntervalSlider.addOnChangeListener { _, value, _ ->
            prefs.forceInterval = value.toInt()
            binding.forceIntervalValue.text = "${value.toInt()} 秒"
        }

        // 服务器配置
        binding.serverIpInput.setText(prefs.serverIp)
        binding.serverPortInput.setText(prefs.serverPort.toString())

        binding.serverIpInput.setOnFocusChangeListener { _, hasFocus ->
            if (!hasFocus) {
                val ip = binding.serverIpInput.text.toString()
                if (ip.isNotBlank()) {
                    prefs.serverIp = ip
                }
            }
        }

        binding.serverPortInput.setOnFocusChangeListener { _, hasFocus ->
            if (!hasFocus) {
                val port = binding.serverPortInput.text.toString().toIntOrNull()
                if (port != null && port in 1..65535) {
                    prefs.serverPort = port
                }
            }
        }
    }
}
