package com.recall.mobile

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.viewpager2.widget.ViewPager2
import com.recall.mobile.adapter.ImagePagerAdapter
import com.recall.mobile.data.AppDatabase
import com.recall.mobile.data.Screenshot
import com.recall.mobile.databinding.ActivityImageViewerBinding
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class ImageViewerActivity : AppCompatActivity() {

    private lateinit var binding: ActivityImageViewerBinding
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
    private var screenshots: List<Screenshot> = emptyList()

    companion object {
        const val EXTRA_POSITION = "extra_position"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityImageViewerBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupToolbar()
        loadImages()
    }

    private fun setupToolbar() {
        binding.toolbar.setNavigationOnClickListener {
            finish()
        }
    }

    private fun loadImages() {
        val startPosition = intent.getIntExtra(EXTRA_POSITION, 0)
        val dao = AppDatabase.getInstance(this).screenshotDao()

        lifecycleScope.launch {
            screenshots = dao.getAll().first()

            val adapter = ImagePagerAdapter(screenshots)
            binding.viewPager.adapter = adapter
            binding.viewPager.setCurrentItem(startPosition, false)

            updateTimestamp(startPosition)

            binding.viewPager.registerOnPageChangeCallback(object : ViewPager2.OnPageChangeCallback() {
                override fun onPageSelected(position: Int) {
                    updateTimestamp(position)
                }
            })
        }
    }

    private fun updateTimestamp(position: Int) {
        if (position in screenshots.indices) {
            val screenshot = screenshots[position]
            binding.toolbar.title = "${position + 1} / ${screenshots.size}"
            binding.timestampText.text = dateFormat.format(Date(screenshot.timestamp))
        }
    }
}
