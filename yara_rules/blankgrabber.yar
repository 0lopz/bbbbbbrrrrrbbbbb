rule BlankGrabber_Stealer {
    meta:
        author = "ratters.rip Team"
        description = "Detects BlankGrabber information stealer with improved coverage"
        reference = "https://github.com/Blank-c/Blank-Grabber"
        date = "2025-04-13"
        version = "2.0"
        tlp = "AMBER"
        severity = "High"
        os = "Windows"
        arch = "x86|x64"

    strings:
        // File artifacts
        $file_config = "config.json" wide ascii
        $file_storage = "storage.json" wide ascii
        $file_logs = "logs.txt" wide ascii
        $file_temp = "temp" wide ascii
        
        // Common strings in binary
        $str_blankgrabber = "BlankGrabber" nocase wide ascii
        $str_webhook = "webhook_url" nocase wide ascii
        $str_antidebug = "anti_debug" nocase wide ascii
        $str_injection = "injection" nocase wide ascii
        
        // API patterns
        $api_discord = /discord(app)?\.com\/api\/webhooks\/\d+\/[a-zA-Z0-9_-]{24,68}/ nocase
        $api_telegram = /api\.telegram\.org\/bot[0-9]{8,10}:[a-zA-Z0-9_-]{30,40}\// nocase
        
        // Function patterns
        $func_grab = "grab_" nocase wide ascii
        $func_steal = "steal_" nocase wide ascii
        $func_send = "send_" nocase wide ascii
        $func_bypass = "bypass_" nocase wide ascii
        
        // Crypto patterns
        $crypto_wallet = /(electrum|exodus|atomic|binance|trust|coinomi|metamask)/ nocase
        
        // Config patterns
        $config_json = /"webhook"\s*:\s*"[^\"]+"/
        $config_autostart = /"autostart"\s*:\s*(true|false)/
        
        // Anti-analysis
        $vm_check = /(virtualbox|vmware|vbox|sandbox|wine)/ nocase
        $debug_check = /(IsDebuggerPresent|CheckRemoteDebugger|OutputDebugString)/

    condition:
        // PE header check for executables
        uint16(0) == 0x5A4D and
        (
            // Strong indicators (3+ matches)
            (4 of ($file_*) and 3 of ($str_*)) or
            // Webhook + grabber functionality
            (any of ($api_*) and 2 of ($func_*)) or
            // Config with specific patterns
            ($config_json and $config_autostart) or
            // Python-specific indicators
            (filesize < 2MB and 3 of ($str_*) and $func_grab) or
            // Anti-analysis behaviors
            ($vm_check and $debug_check)
        )
}