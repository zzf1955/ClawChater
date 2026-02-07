package com.recall.mobile.data

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Dao
interface ScreenshotDao {
    @Insert
    suspend fun insert(screenshot: Screenshot): Long

    @Query("SELECT * FROM screenshots ORDER BY timestamp DESC")
    fun getAll(): Flow<List<Screenshot>>

    @Query("SELECT * FROM screenshots WHERE syncStatus = 'pending' ORDER BY timestamp ASC")
    suspend fun getPendingSync(): List<Screenshot>

    @Query("UPDATE screenshots SET syncStatus = :status WHERE id = :id")
    suspend fun updateSyncStatus(id: Long, status: String)

    @Query("SELECT COUNT(*) FROM screenshots")
    suspend fun getCount(): Int

    @Delete
    suspend fun delete(screenshot: Screenshot)

    @Query("DELETE FROM screenshots WHERE syncStatus = 'synced' AND timestamp < :beforeTimestamp")
    suspend fun deleteSyncedBefore(beforeTimestamp: Long)
}
