package com.recall.mobile.adapter

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.bumptech.glide.Glide
import com.recall.mobile.data.Screenshot
import com.recall.mobile.databinding.ItemScreenshotBinding
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class ScreenshotAdapter(
    private val onItemClick: (Screenshot, Int) -> Unit
) : ListAdapter<Screenshot, ScreenshotAdapter.ViewHolder>(DiffCallback()) {

    private val dateFormat = SimpleDateFormat("MM-dd HH:mm:ss", Locale.getDefault())

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemScreenshotBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position), position)
    }

    inner class ViewHolder(
        private val binding: ItemScreenshotBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(screenshot: Screenshot, position: Int) {
            binding.timestampText.text = dateFormat.format(Date(screenshot.timestamp))

            Glide.with(binding.thumbnailImage)
                .load(File(screenshot.path))
                .centerCrop()
                .into(binding.thumbnailImage)

            binding.root.setOnClickListener {
                onItemClick(screenshot, position)
            }
        }
    }

    class DiffCallback : DiffUtil.ItemCallback<Screenshot>() {
        override fun areItemsTheSame(oldItem: Screenshot, newItem: Screenshot): Boolean {
            return oldItem.id == newItem.id
        }

        override fun areContentsTheSame(oldItem: Screenshot, newItem: Screenshot): Boolean {
            return oldItem == newItem
        }
    }
}
