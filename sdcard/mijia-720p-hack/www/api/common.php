<?php
/**
 * Mijia 720p Hack - API Common Utilities
 * Author: Antigravity / Jan Sperling / Community
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit(0);
}

/**
 * Execute a command within the context of functions.sh
 */
function run_shell_func($cmd) {
    $script = '/tmp/sd/mijia-720p-hack/scripts/functions.sh';
    if (!file_exists($script)) {
        // Fallback relative path
        $script = realpath(dirname(__FILE__) . '/../../scripts/functions.sh');
    }
    
    // Source functions.sh and run command
    $fullCmd = ". {$script} >/dev/null 2>&1; " . $cmd . " 2>&1";
    $output = shell_exec($fullCmd);
    return trim($output);
}

/**
 * Get request parameters merging GET, POST, and JSON body
 */
function get_params() {
    $params = array_merge($_GET, $_POST);
    $input = file_get_contents('php://input');
    if (!empty($input)) {
        $json = json_decode($input, true);
        if (is_array($json)) {
            $params = array_merge($params, $json);
        }
    }
    return $params;
}

/**
 * Send JSON response and exit
 */
function send_json($data, $code = 200) {
    http_response_code($code);
    echo json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    exit;
}

/**
 * Send error response
 */
function send_error($message, $code = 400) {
    send_json(array(
        'status' => 'error',
        'message' => $message
    ), $code);
}
