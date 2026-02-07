package com.recall.mobile

import android.app.Application
import com.recall.mobile.data.AppDatabase

class RecallApp : Application() {

    val database: AppDatabase by lazy { AppDatabase.getInstance(this) }

    override fun onCreate() {
        super.onCreate()
        instance = this
    }

    companion object {
        lateinit var instance: RecallApp
            private set
    }
}
