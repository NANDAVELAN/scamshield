package com.scamshield.app

import android.app.Notification
import android.os.Bundle
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

class ScamNotificationListenerService : NotificationListenerService() {

    private val TAG = "ScamShieldListener"
    private val scope = CoroutineScope(Dispatchers.IO)

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        super.onNotificationPosted(sbn)
        if (sbn == null) return

        val pkg = sbn.packageName
        // Ignore our own notifications
        if (pkg == packageName) return

        val channel = when (pkg) {
            "com.whatsapp" -> "whatsapp"
            "com.google.android.gm" -> "gmail"
            "com.google.android.apps.messaging",
            "com.android.mms",
            "com.samsung.android.messaging" -> "sms"
            else -> return // Ignore unrelated packages
        }

        val extras: Bundle = sbn.notification.extras ?: return
        val title = extras.getString(Notification.EXTRA_TITLE) ?: extras.getCharSequence(Notification.EXTRA_TITLE)?.toString() ?: "Unknown"
        val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString() 
            ?: extras.getCharSequence(Notification.EXTRA_BIG_TEXT)?.toString() 
            ?: ""

        if (text.isBlank()) return

        val timestamp = sbn.postTime

        Log.d(TAG, "Captured notification from $channel ($pkg): $title")

        // 1. Notify Capacitor Webview if running
        NotificationBridgePlugin.notifyMessage(channel, title, text, timestamp)

        // 2. Perform background analysis to defend user even if app is closed
        scope.launch {
            try {
                // Default local emulator or LAN backend
                val backendUrl = "http://10.0.2.2:8000/analyze"
                val jsonPayload = JSONObject().apply {
                    put("id", "notif_${System.currentTimeMillis()}")
                    put("channel", channel)
                    put("sender", title)
                    put("body", text)
                    put("timestamp", timestamp)
                }

                val url = URL(backendUrl)
                val conn = (url.openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"
                    setRequestProperty("Content-Type", "application/json")
                    doOutput = true
                    connectTimeout = 3000
                    readTimeout = 3000
                }

                OutputStreamWriter(conn.outputStream).use { writer ->
                    writer.write(jsonPayload.toString())
                    writer.flush()
                }

                if (conn.responseCode == 200) {
                    val responseStr = conn.inputStream.bufferedReader().use { it.readText() }
                    val verdictObj = JSONObject(responseStr)
                    val verdict = verdictObj.optString("verdict", "safe")

                    if (verdict == "scam") {
                        Log.i(TAG, "SCAM DETECTED from $title! Canceling notification.")
                        // Cancel original notification where permitted
                        try {
                            cancelNotification(sbn.key)
                        } catch (e: Exception) {
                            Log.w(TAG, "Could not cancel notification: ${e.message}")
                        }

                        // Post our own alert without the scam body
                        NotificationBridgePlugin.instance?.let { plugin ->
                            val callObj = com.getcapacitor.JSObject().apply {
                                put("sender", title)
                            }
                            // Post high priority shield notification
                            val dummyCall = com.getcapacitor.PluginCall(
                                plugin.bridge.msgHandler,
                                "NotificationBridge",
                                "dummyCallback",
                                "postBlockNotification",
                                callObj
                            )
                            plugin.postBlockNotification(dummyCall)
                        }
                    }
                }
            } catch (e: Exception) {
                Log.d(TAG, "Background check completed or offline: ${e.message}")
            }
        }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification?) {
        super.onNotificationRemoved(sbn)
    }
}
