<?php
/**
 * Mijia 720p Hack - System Management & Service Control API
 * Author: Antigravity / Jan Sperling / Community
 */

require_once __DIR__ . '/common.php';

$params = get_params();
$action = isset($params['action']) ? strtolower(trim($params['action'])) : 'status';

function fetch_system_info() {
    $raw = run_shell_func('system_status');
    $decoded = json_decode($raw, true);
    if (is_array($decoded) && isset($decoded['system'])) {
        return $decoded['system'];
    }
    return array('raw' => $raw);
}

switch ($action) {
    case 'status':
    case 'info':
        send_json(array(
            'status' => 'ok',
            'action' => 'status',
            'system' => fetch_system_info()
        ));
        break;

    case 'reboot':
        // Run reboot in background after 1s so response completes
        shell_exec('(sleep 1; /sbin/reboot) >/dev/null 2>&1 &');
        send_json(array(
            'status' => 'ok',
            'action' => 'reboot',
            'message' => 'Camera is rebooting...'
        ));
        break;

    case 'service':
        $service = isset($params['name']) ? strtolower(trim($params['name'])) : '';
        $cmd = isset($params['cmd']) ? strtolower(trim($params['cmd'])) : 'status';

        $allowed_cmds = array('start', 'stop', 'restart', 'status');
        if (!in_array($cmd, $allowed_cmds)) {
            send_error('Invalid command. Allowed: start, stop, restart, status');
        }

        $script_map = array(
            'rtsp'            => '/tmp/sd/mijia-720p-hack/scripts/S99rtsp',
            'ssh'             => '/tmp/sd/mijia-720p-hack/scripts/S99dropbear',
            'dropbear'        => '/tmp/sd/mijia-720p-hack/scripts/S99dropbear',
            'ftp'             => '/tmp/sd/mijia-720p-hack/scripts/S99ftpd',
            'ftpd'            => '/tmp/sd/mijia-720p-hack/scripts/S99ftpd',
            'samba'           => '/tmp/sd/mijia-720p-hack/scripts/S99samba',
            'lighttpd'        => '/tmp/sd/mijia-720p-hack/scripts/S99lighttpd',
            'http'            => '/tmp/sd/mijia-720p-hack/scripts/S99lighttpd',
            'cloud'           => '/tmp/sd/mijia-720p-hack/scripts/S50disable_cloud',
            'ota'             => '/tmp/sd/mijia-720p-hack/scripts/S50disable_ota',
            'auto_night_mode' => '/tmp/sd/mijia-720p-hack/scripts/S99auto_night_mode'
        );

        if (!isset($script_map[$service])) {
            send_error('Invalid service name: ' . $service);
        }

        $scriptPath = $script_map[$service];
        $output = shell_exec("{$scriptPath} {$cmd} 2>&1");
        
        send_json(array(
            'status' => 'ok',
            'action' => 'service',
            'service' => $service,
            'command' => $cmd,
            'output' => trim($output),
            'system' => fetch_system_info()
        ));
        break;

    default:
        send_error("Unknown action: {$action}");
        break;
}
