<?php
/**
 * Mijia 720p Hack - Settings Configuration API
 * Author: Antigravity / Jan Sperling / Community
 */

require_once __DIR__ . '/common.php';

$cfgPath = '/tmp/sd/mijia-720p-hack.cfg';
if (!file_exists($cfgPath)) {
    // Relative fallback
    $cfgPath = realpath(dirname(__FILE__) . '/../../../mijia-720p-hack.cfg');
}

function parse_cfg_file($path) {
    $settings = array();
    if (!file_exists($path)) {
        return $settings;
    }
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        $line = trim($line);
        if (empty($line) || $line[0] === '#') {
            continue;
        }
        $parts = explode('=', $line, 2);
        if (count($parts) === 2) {
            $key = trim($parts[0]);
            $val = trim($parts[1]);
            // Strip quotes
            $val = trim($val, '"\'');
            $settings[$key] = $val;
        }
    }
    return $settings;
}

function save_cfg_file($path, $newValues) {
    if (!file_exists($path)) {
        // Create if not exists
        touch($path);
    }
    $lines = file($path, FILE_IGNORE_NEW_LINES);
    $keysFound = array();
    $output = array();

    foreach ($lines as $line) {
        $trimmed = trim($line);
        if (empty($trimmed) || $trimmed[0] === '#') {
            $output[] = $line;
            continue;
        }
        $parts = explode('=', $trimmed, 2);
        if (count($parts) === 2) {
            $k = trim($parts[0]);
            if (array_key_exists($k, $newValues)) {
                $val = $newValues[$k];
                // Quote string values or values with spaces
                $output[] = "{$k}=\"{$val}\"";
                $keysFound[$k] = true;
            } else {
                $output[] = $line;
            }
        } else {
            $output[] = $line;
        }
    }

    // Add any new keys that weren't in file
    foreach ($newValues as $k => $v) {
        if (!isset($keysFound[$k])) {
            $output[] = "{$k}=\"{$v}\"";
        }
    }

    file_put_contents($path, implode("\n", $output) . "\n");
    return true;
}

$params = get_params();
$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'GET') {
    $current = parse_cfg_file($cfgPath);
    // Don't send root password in plain text if masked requested
    send_json(array(
        'status' => 'ok',
        'config' => $current
    ));
} elseif ($method === 'POST') {
    // Whitelist of valid config keys
    $validKeys = array(
        'ROOT_PASSWORD', 'WIFI_SSID', 'WIFI_PASS', 'TIMEZONE', 'NTP_SERVER',
        'ENABLE_SYSLOG', 'DISABLE_CLOUD', 'DISABLE_OTA', 'ENABLE_TELNETD',
        'ENABLE_SSHD', 'ENABLE_HTTPD', 'ENABLE_FTPD', 'ENABLE_SAMBA',
        'ENABLE_RTSP', 'DISABLE_HACK', 'SOUND_EN'
    );

    $toSave = array();
    foreach ($validKeys as $k) {
        if (isset($params[$k])) {
            $val = trim($params[$k]);
            $toSave[$k] = $val;
        }
    }

    if (empty($toSave)) {
        send_error('No valid settings provided to update');
    }

    save_cfg_file($cfgPath, $toSave);

    // If WiFi settings provided, run configure_wifi script
    if (isset($toSave['WIFI_SSID']) && !empty($toSave['WIFI_SSID'])) {
        $wifiScript = '/tmp/sd/mijia-720p-hack/scripts/configure_wifi';
        if (file_exists($wifiScript)) {
            $ssid = escapeshellarg($toSave['WIFI_SSID']);
            $pass = isset($toSave['WIFI_PASS']) ? escapeshellarg($toSave['WIFI_PASS']) : "''";
            shell_exec("{$wifiScript} {$ssid} {$pass} >/dev/null 2>&1 &");
        }
    }

    // If root password provided, update system shadow/passwd if possible
    if (isset($toSave['ROOT_PASSWORD']) && !empty($toSave['ROOT_PASSWORD'])) {
        $pwd = escapeshellarg($toSave['ROOT_PASSWORD']);
        shell_exec("echo \"root:{$pwd}\" | chpasswd >/dev/null 2>&1");
    }

    send_json(array(
        'status' => 'ok',
        'message' => 'Settings saved successfully',
        'config' => parse_cfg_file($cfgPath)
    ));
} else {
    send_error('Method not allowed', 405);
}
