package com.scamshield.app

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.provider.Settings
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.getcapacitor.JSObject
import com.getcapacitor.Plugin
import com.getcapacitor.PluginCall
import com.getcapacitor.PluginMethod
import com.getcapacitor.annotation.CapacitorPlugin

@CapacitorPlugin(name = "NotificationBridge")
class NotificationBridgePlugin : Plugin() {

    companion object {
        var instance: NotificationBridgePlugin? = null
        const val CHANNEL_ID = "scamshield_alerts"

        fun notifyMessage(channel: String, sender: String, body: String, timestamp: Long) {
            instance?.let { plugin ->
                val data = JSObject().apply {
                    put("channel", channel)
                    put("sender", sender)
                    put("body", body)
                    put("timestamp", timestamp)
                }
                plugin.notifyListeners("messageReceived", data)
            }
        }
    }

    override fun load() {
        super.load()
        instance = this
        createNotificationChannel()
    }

    @PluginMethod
    fun isAccessGranted(call: PluginCall) {
        val context = context
        val enabledPackages = NotificationManagerCompat.getEnabledListenerPackages(context)
        val granted = enabledPackages.contains(context.packageName)
        val ret = JSObject()
        ret.put("granted", granted)
        call.resolve(ret)
    }

    @PluginMethod
    fun openAccessSettings(call: PluginCall) {
        try {
            val intent = Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(intent)
            call.resolve()
        } catch (e: Exception) {
            call.reject("Could not open notification settings", e)
        }
    }

    @PluginMethod
    fun postBlockNotification(call: PluginCall) {
        val sender = call.getString("sender") ?: "Unknown"
        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.stat_sys_warning)
            .setContentTitle("🛡️ ScamShield Alert")
            .setContentText("ScamShield blocked a scam from $sender")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .build()

        notificationManager.notify((System.currentTimeMillis() % 10000).toInt(), notification)
        call.resolve()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val name = "ScamShield Defense Alerts"
            val descriptionText = "Notifications for blocked and warned scam messages"
            val importance = NotificationManager.IMPORTANCE_HIGH
            val channel = NotificationChannel(CHANNEL_ID, name, importance).apply {
                description = descriptionText
            }
            val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }
}
