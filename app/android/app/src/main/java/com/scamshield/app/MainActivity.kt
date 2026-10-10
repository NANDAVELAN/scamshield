package com.scamshield.app

import android.os.Bundle
import com.getcapacitor.BridgeActivity

class MainActivity : BridgeActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        registerPlugin(NotificationBridgePlugin::class.java)
        super.onCreate(savedInstanceState)
    }
}
