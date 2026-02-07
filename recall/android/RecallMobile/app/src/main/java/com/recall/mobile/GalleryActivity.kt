package com.recall.mobile

import android.content.Intent
import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.GridLayoutManager
import com.recall.mobile.adapter.ScreenshotAdapter
import com.recall.mobile.data.AppDatabase
import com.recall.mobile.databinding.ActivityGalleryBinding
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class GalleryActivity : AppCompatActivity() {

    private lateinit var binding: ActivityGalleryBinding
    private lateinit var adapter: ScreenshotAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityGalleryBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupToolbar()
        setupRecyclerView()
        loadScreenshots()
    }

    private fun setupToolbar() {
        binding.toolbar.setNavigationOnClickListener {
            finish()
        }
    }

    private fun setupRecyclerView() {
        adapter = ScreenshotAdapter { _, position ->
            val intent = Intent(this, ImageViewerActivity::class.java).apply {
                putExtra(ImageViewerActivity.EXTRA_POSITION, position)
            }
            startActivity(intent)
        }

        binding.recyclerView.apply {
            layoutManager = GridLayoutManager(this@GalleryActivity, 2)
            adapter = this@GalleryActivity.adapter
        }
    }

    private fun loadScreenshots() {
        val dao = AppDatabase.getInstance(this).screenshotDao()

        lifecycleScope.launch {
            dao.getAll().collectLatest { screenshots ->
                adapter.submitList(screenshots)
                binding.emptyText.visibility = if (screenshots.isEmpty()) View.VISIBLE else View.GONE
            }
        }
    }
}
