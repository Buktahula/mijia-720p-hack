<?php
/**
 * Mijia 720p Hack - Motor / PTZ Control API
 * Author: Antigravity / Jan Sperling / Community
 */

require_once __DIR__ . '/common.php';

$params = get_params();
$action = isset($params['action']) ? strtolower(trim($params['action'])) : 'status';

function fetch_motor_status() {
    $raw = run_shell_func('motor status');
    $decoded = json_decode($raw, true);
    if (is_array($decoded) && isset($decoded['motor'])) {
        return $decoded['motor'];
    }
    // Fallback if raw JSON parse failed
    return array('raw' => $raw);
}

function fetch_presets() {
    $raw = run_shell_func('motor get_presets');
    $decoded = json_decode($raw, true);
    if (is_array($decoded)) {
        return $decoded;
    }
    return array('raw' => $raw);
}

switch ($action) {
    case 'status':
        send_json(array(
            'status' => 'ok',
            'action' => 'status',
            'motor' => fetch_motor_status(),
            'presets' => fetch_presets()
        ));
        break;

    case 'move':
        $dir = isset($params['dir']) ? strtolower(trim($params['dir'])) : '';
        $allowed = array('up', 'down', 'left', 'right');
        if (!in_array($dir, $allowed)) {
            send_error('Invalid direction. Allowed: up, down, left, right');
        }
        $step = isset($params['step']) ? intval($params['step']) : 1;
        if ($step < 1) $step = 1;
        if ($step > 15) $step = 15;

        run_shell_func("motor {$dir} {$step}");
        send_json(array(
            'status' => 'ok',
            'action' => 'move',
            'direction' => $dir,
            'step' => $step,
            'motor' => fetch_motor_status()
        ));
        break;

    case 'goto':
        if (!isset($params['x']) || !isset($params['y'])) {
            send_error('Parameters x (0..31) and y (0..15) are required for goto');
        }
        $x = intval($params['x']);
        $y = intval($params['y']);
        if ($x < 0) $x = 0; if ($x > 31) $x = 31;
        if ($y < 0) $y = 0; if ($y > 15) $y = 15;

        run_shell_func("motor goto {$x} {$y}");
        send_json(array(
            'status' => 'ok',
            'action' => 'goto',
            'target' => array('x' => $x, 'y' => $y),
            'motor' => fetch_motor_status()
        ));
        break;

    case 'center':
        run_shell_func('motor center');
        send_json(array(
            'status' => 'ok',
            'action' => 'center',
            'motor' => fetch_motor_status()
        ));
        break;

    case 'calibrate':
        run_shell_func('motor calibrate');
        send_json(array(
            'status' => 'ok',
            'action' => 'calibrate',
            'motor' => fetch_motor_status()
        ));
        break;

    case 'preset':
        $id = isset($params['id']) ? intval($params['id']) : 1;
        if ($id < 1 || $id > 4) {
            send_error('Preset id must be between 1 and 4');
        }
        run_shell_func("motor preset {$id}");
        send_json(array(
            'status' => 'ok',
            'action' => 'preset',
            'preset_id' => $id,
            'motor' => fetch_motor_status()
        ));
        break;

    case 'set_preset':
        $id = isset($params['id']) ? intval($params['id']) : 1;
        if ($id < 1 || $id > 4) {
            send_error('Preset id must be between 1 and 4');
        }
        run_shell_func("motor set_preset {$id}");
        send_json(array(
            'status' => 'ok',
            'action' => 'set_preset',
            'preset_id' => $id,
            'presets' => fetch_presets(),
            'motor' => fetch_motor_status()
        ));
        break;

    case 'presets':
    case 'get_presets':
        send_json(array(
            'status' => 'ok',
            'action' => 'get_presets',
            'presets' => fetch_presets()
        ));
        break;

    default:
        send_error("Unknown action: {$action}");
        break;
}
