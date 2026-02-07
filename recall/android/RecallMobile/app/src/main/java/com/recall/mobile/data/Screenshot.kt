package com.recall.mobile.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "screenshots")
data class Screenshot(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val path: String,
    val timestamp: Long,
    val syncStatus: String = "pending",  // pending, synced, error
    val createdAt: Long = System.currentTimeMillis()
)
