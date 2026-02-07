package com.recall.mobile.adapter

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.bumptech.glide.Glide
import com.github.chrisbanes.photoview.PhotoView
import com.recall.mobile.R
import com.recall.mobile.data.Screenshot
import java.io.File

class ImagePagerAdapter(
    private val screenshots: List<Screenshot>
) : RecyclerView.Adapter<ImagePagerAdapter.ViewHolder>() {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val photoView = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_image_viewer, parent, false) as PhotoView
        return ViewHolder(photoView)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(screenshots[position])
    }

    override fun getItemCount(): Int = screenshots.size

    class ViewHolder(private val photoView: PhotoView) : RecyclerView.ViewHolder(photoView) {
        fun bind(screenshot: Screenshot) {
            Glide.with(photoView)
                .load(File(screenshot.path))
                .into(photoView)
        }
    }
}
