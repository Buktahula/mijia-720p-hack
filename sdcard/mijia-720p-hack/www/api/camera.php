<?php
/**
 * Mijia 720p Hack - Camera & Hardware Control API
 * Author: Antigravity / Jan Sperling / Community
 */

require_once __DIR__ . '/common.php';

$params = get_params();
$action = isset($params['action']) ? strtolower(trim($params['action'])) : 'status';

function fetch_camera_status() {
    $nm_raw = run_shell_func('night_mode status');
    $nm_json = json_decode($nm_raw, true);

    $ir_raw = run_shell_func('ir_led status');
    $ir_json = json_decode($ir_raw, true);

    $cut_raw = run_shell_func('ir_cut status');
    $cut_json = json_decode($cut_raw, true);

    $flip_raw = run_shell_func('flip status');
    $flip_json = json_decode($flip_raw, true);

    $mir_raw = run_shell_func('mirror status');
    $mir_json = json_decode($mir_raw, true);

    $b_raw = run_shell_func('blue_led status');
    $b_json = json_decode($b_raw, true);

    $y_raw = run_shell_func('yellow_led status');
    $y_json = json_decode($y_raw, true);

    return array(
        'night_mode' => isset($nm_json['night_mode']) ? $nm_json['night_mode'] : null,
        'night_mode_nvram' => isset($nm_json['nvram']) ? $nm_json['nvram'] : null,
        'auto_night' => isset($nm_json['auto']) ? $nm_json['auto'] : 'off',
        'ir_led' => isset($ir_json['ir_led']) ? intval($ir_json['ir_led']) : 0,
        'ir_cut' => isset($cut_json['ir_cut']) ? $cut_json['ir_cut'] : null,
        'flip' => isset($flip_json['flip']) ? $flip_json['flip'] : null,
        'mirror' => isset($mir_json['mirror']) ? $mir_json['mirror'] : null,
        'blue_led' => isset($b_json['blue_led']) ? $b_json['blue_led'] : 'off',
        'yellow_led' => isset($y_json['yellow_led']) ? $y_json['yellow_led'] : 'off'
    );
}

switch ($action) {
    case 'status':
        send_json(array(
            'status' => 'ok',
            'action' => 'status',
            'camera' => fetch_camera_status()
        ));
        break;

    case 'night_mode':
        $mode = isset($params['mode']) ? strtolower(trim($params['mode'])) : '';
        if ($mode === 'day') $mode = 'off';
        if ($mode === 'night') $mode = 'on';
        if (!in_array($mode, array('auto', 'on', 'off'))) {
            send_error('Invalid night mode. Allowed: auto, on, off');
        }
        run_shell_func("night_mode {$mode}");
        send_json(array(
            'status' => 'ok',
            'action' => 'night_mode',
            'mode' => $mode,
            'camera' => fetch_camera_status()
        ));
        break;

    case 'ir_led':
        if (!isset($params['value'])) {
            send_error('Parameter value is required (0..255, on, off)');
        }
        $val = trim($params['value']);
        if ($val === 'on') $val = 255;
        if ($val === 'off') $val = 0;
        $num = intval($val);
        if ($num < 0) $num = 0;
        if ($num > 255) $num = 255;
        run_shell_func("ir_led {$num}");
        send_json(array(
            'status' => 'ok',
            'action' => 'ir_led',
            'value' => $num,
            'camera' => fetch_camera_status()
        ));
        break;

    case 'ir_cut':
        $state = isset($params['state']) ? strtolower(trim($params['state'])) : '';
        if ($state === '1') $state = 'on';
        if ($state === '0') $state = 'off';
        if (!in_array($state, array('on', 'off'))) {
            send_error('Invalid ir_cut state. Allowed: on, off');
        }
        run_shell_func("ir_cut {$state}");
        send_json(array(
            'status' => 'ok',
            'action' => 'ir_cut',
            'state' => $state,
            'camera' => fetch_camera_status()
        ));
        break;

    case 'flip':
        $state = isset($params['state']) ? strtolower(trim($params['state'])) : '';
        if ($state === '1') $state = 'on';
        if ($state === '0') $state = 'off';
        if (!in_array($state, array('on', 'off'))) {
            send_error('Invalid flip state. Allowed: on, off');
        }
        run_shell_func("flip {$state}");
        send_json(array(
            'status' => 'ok',
            'action' => 'flip',
            'state' => $state,
            'camera' => fetch_camera_status()
        ));
        break;

    case 'mirror':
        $state = isset($params['state']) ? strtolower(trim($params['state'])) : '';
        if ($state === '1') $state = 'on';
        if ($state === '0') $state = 'off';
        if (!in_array($state, array('on', 'off'))) {
            send_error('Invalid mirror state. Allowed: on, off');
        }
        run_shell_func("mirror {$state}");
        send_json(array(
            'status' => 'ok',
            'action' => 'mirror',
            'state' => $state,
            'camera' => fetch_camera_status()
        ));
        break;

    case 'led':
        $color = isset($params['color']) ? strtolower(trim($params['color'])) : '';
        $state = isset($params['state']) ? strtolower(trim($params['state'])) : '';
        if (!in_array($color, array('blue', 'yellow'))) {
            send_error('Invalid LED color. Allowed: blue, yellow');
        }
        if (!in_array($state, array('on', 'off', 'blink'))) {
            send_error('Invalid LED state. Allowed: on, off, blink');
        }
        run_shell_func("{$color}_led {$state}");
        send_json(array(
            'status' => 'ok',
            'action' => 'led',
            'color' => $color,
            'state' => $state,
            'camera' => fetch_camera_status()
        ));
        break;

    default:
        send_error("Unknown action: {$action}");
        break;
}
